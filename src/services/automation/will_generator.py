# src/services/automation/will_generator.py

import pandas as pd
import numpy as np
from io import BytesIO
from typing import List, Tuple, Dict, Any
from datetime import datetime
from docx import Document
from docx.shared import Pt, Mm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from PIL import Image, ImageOps, ImageChops
from pypdf import PdfReader
from pdf2image import convert_from_bytes

from src.legal_system.core.ai_factory import AIFactory
from src.legal_system.core.schemas import WillDraftStructure

class WillDraftGenerator:
    def __init__(self):
        self.llm = AIFactory.get_llm(mode="cloud", temperature=0.0)

    def generate_draft(self, excel_file: BytesIO, template_file: BytesIO, registry_files: List[Any] = None) -> Tuple[BytesIO, WillDraftStructure, str]:
        """
        遺言書生成のメイン処理
        Args:
            registry_files: StreamlitのUploadedFileオブジェクトのリスト
        """
        # 1. Excel解析
        excel_file.seek(0)
        if hasattr(excel_file, 'name') and excel_file.name.endswith('.xlsx'):
            df = pd.read_excel(excel_file)
        else:
            df = pd.read_csv(excel_file)

        # データ補完（結合セル対策）
        df = df.replace(r'^\s*$', np.nan, regex=True).ffill()
        if 'No' in df.columns:
            df = df.dropna(subset=['No'])

        if df.empty:
            raise ValueError("有効なデータ行がありません。")

        csv_text = df.fillna("").to_csv(index=False)

        # 2. 登記情報の処理 (画像化 + テキスト抽出)
        registry_data = self._process_registry_files(registry_files)

        # 3. AI推論
        draft_data = self._invoke_ai_reasoning(csv_text)

        # 4. Word生成
        template_file.seek(0)
        safe_template = BytesIO(template_file.read())
        output_doc = self._create_word_document_clean(safe_template, draft_data, registry_data)
        
        output_stream = BytesIO()
        output_doc.save(output_stream)
        output_stream.seek(0)
        
        return output_stream, draft_data, csv_text

    def _process_registry_files(self, files: List[Any]) -> Dict[str, Any]:
        """
        アップロードされた登記情報(PDF/画像)を処理する
        - 画像への変換 & 余白トリミング
        - PDFからのテキスト抽出
        """
        processed = {"images": [], "text": ""}
        if not files:
            return processed

        full_text = []
        
        for f in files:
            f.seek(0)
            file_bytes = f.read()
            file_name = getattr(f, "name", "unknown")

            # PDFの場合
            if file_name.lower().endswith(".pdf") or f.type == "application/pdf":
                # 1. テキスト抽出
                try:
                    reader = PdfReader(BytesIO(file_bytes))
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text()
                    if text.strip():
                        full_text.append(f"【ファイル名: {file_name}】\n{text}\n")
                except Exception as e:
                    print(f"Text extract error: {e}")

                # 2. 画像変換
                try:
                    # dpiを上げて鮮明に
                    pil_images = convert_from_bytes(file_bytes, dpi=200)
                    for img in pil_images:
                        trimmed = self._trim_whitespace(img)
                        buf = BytesIO()
                        trimmed.save(buf, format="JPEG")
                        processed["images"].append(BytesIO(buf.getvalue()))
                except Exception as e:
                    print(f"Image convert error: {e}")

            # 画像の場合
            else:
                try:
                    img = Image.open(BytesIO(file_bytes))
                    trimmed = self._trim_whitespace(img)
                    buf = BytesIO()
                    trimmed.save(buf, format="JPEG")
                    processed["images"].append(BytesIO(buf.getvalue()))
                except Exception as e:
                    print(f"Image load error: {e}")

        processed["text"] = "\n--------------------------------------------------\n".join(full_text)
        return processed

    def _trim_whitespace(self, img: Image.Image) -> Image.Image:
        """画像の白い余白を自動で削除する"""
        try:
            bg = Image.new(img.mode, img.size, (255, 255, 255))
            diff = ImageChops.difference(img, bg)
            diff = ImageChops.add(diff, diff, 2.0, -100)
            bbox = diff.getbbox()
            if bbox:
                return img.crop(bbox)
        except Exception:
            pass
        return img

    def _invoke_ai_reasoning(self, input_text: str) -> WillDraftStructure:
        system_content = """
        あなたは熟練した行政書士です。提供された「遺産整理要旨」に基づき、公正証書遺言の条文案を作成してください。

        # 入力データについて
        - CSV形式のデータを入力します。結合セルは補完済みです。

        # 【重要】条文作成ルール
        1. **予備的遺言の扱い**:
           - **Excelデータに「予備的条項」等の記載がある場合のみ**作成してください。
           - AIが勝手に予備的遺言を創作・提案することは**禁止**します。

        2. **孫への継承（相続 vs 遺贈）**:
           - 受取人が「孫」であり、かつ「相続させる」という指示がある場合は、条文自体は指示通り作成しつつ、**条文の末尾に『（※要確認：孫への承継は通常「遺贈」となります。養子縁組等がないか確認してください）』という注記を必ず追記してください。**

        3. **遺言執行者の指定**:
           - 指定がある場合は、「行政書士法人チェスター（所在：東京都中央区八重洲一丁目7番20号）」を指定してください。
           - **代表者名は記載しないでください**（法人名と所在地のみ）。

        4. **祭祀主宰・付言事項**:
           - Excelデータに具体的な内容（特定の人物名やメッセージ）が記載されている場合のみ作成してください。
           - 空欄の場合や、単に「チェスター」とだけ書かれている場合は、条文を作成しないでください（出力しないでください）。

        5. **不動産の記載**:
           - 所在、地番、家屋番号などは要旨の通り正確に記載すること。

        出力は指定されたJSONスキーマに厳密に従ってください。
        """
        
        parser = PydanticOutputParser(pydantic_object=WillDraftStructure)
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=system_content),
            HumanMessagePromptTemplate.from_template(
                "以下の要旨データに基づき、遺言書ドラフトを作成してください。\n\n【要旨データ】\n{input_text}\n\n【出力形式】\n{format_instructions}"
            )
        ])
        
        chain = prompt | self.llm | parser
        
        return chain.invoke({
            "input_text": input_text,
            "format_instructions": parser.get_format_instructions()
        })

    def _set_jp_font(self, run, size_pt=12, is_bold=False):
        try:
            run.font.name = "MS Mincho"
            run.font.size = Pt(size_pt)
            run.font.bold = is_bold
            run._element.rPr.rFonts.set(qn('w:eastAsia'), 'ＭＳ 明朝')
            run._element.rPr.rFonts.set(qn('w:ascii'), 'MS Mincho')
            run._element.rPr.rFonts.set(qn('w:hAnsi'), 'MS Mincho')
        except Exception:
            pass

    def _create_word_document_clean(self, template_file: BytesIO, data: WillDraftStructure, registry_data: Dict[str, Any]) -> Document:
        try:
            doc = Document(template_file)
            if doc._body:
                doc._body.clear_content()
        except Exception:
            doc = Document()

        # タイトル
        p_main = doc.add_paragraph()
        p_main.alignment = WD_ALIGN_PARAGRAPH.CENTER
        self._set_jp_font(p_main.add_run("遺言公正証書（案）"), size_pt=18, is_bold=True)
        doc.add_paragraph("")

        # 作成日時
        p_date = doc.add_paragraph()
        p_date.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        timestamp = datetime.now().strftime('%Y年%m月%d日 作成')
        self._set_jp_font(p_date.add_run(timestamp), size_pt=10.5)
        doc.add_paragraph("") 

        if not data.articles:
            doc.add_paragraph("※ 生成された条文データがありません。要旨の内容を確認してください。")
            return doc

        # 条文書き込み
        for article in data.articles:
            p_title = doc.add_paragraph()
            self._set_jp_font(p_title.add_run(f"{article.article_number}"), size_pt=12, is_bold=True)
            if article.title:
                self._set_jp_font(p_title.add_run(f"　（{article.title}）"), size_pt=12, is_bold=True)
            
            p_content = doc.add_paragraph()
            p_content.paragraph_format.first_line_indent = Mm(5)
            
            content_text = article.content if article.content else ""
            
            # 注記（孫への確認等）が含まれる場合、赤字にする処理
            if "※要確認" in content_text:
                parts = content_text.split("（※要確認")
                # 通常部分
                self._set_jp_font(p_content.add_run(parts[0]), size_pt=12)
                # 注記部分
                if len(parts) > 1:
                    run_alert = p_content.add_run(f"（※要確認{parts[1]}")
                    self._set_jp_font(run_alert, size_pt=12, is_bold=True)
                    run_alert.font.color.rgb = RGBColor(255, 0, 0) # 赤色
            else:
                self._set_jp_font(p_content.add_run(content_text), size_pt=12)
            
            doc.add_paragraph("")

        # 付言事項
        if data.supplementary_provisions:
            p_head = doc.add_paragraph()
            self._set_jp_font(p_head.add_run("（付言事項）"), size_pt=12, is_bold=True)
            p_body = doc.add_paragraph()
            p_body.paragraph_format.first_line_indent = Mm(5)
            self._set_jp_font(p_body.add_run(data.supplementary_provisions), size_pt=12)

        # --- 【別紙】登記情報 (画像) ---
        images = registry_data.get("images", [])
        if images:
            doc.add_page_break()
            p_h = doc.add_paragraph()
            p_h.alignment = WD_ALIGN_PARAGRAPH.CENTER
            self._set_jp_font(p_h.add_run("【別紙】不動産登記情報（画像）"), size_pt=14, is_bold=True)
            doc.add_paragraph("") 

            for img_data in images:
                try:
                    img_data.seek(0)
                    doc.add_picture(img_data, width=Mm(170))
                    # 余白削除により詰まっているので、最低限の改行のみ
                    doc.add_paragraph("") 
                except Exception as e:
                    doc.add_paragraph(f"※画像エラー: {e}")

        # --- 【参考】登記情報 (テキスト) ---
        text_data = registry_data.get("text", "")
        if text_data:
            doc.add_page_break()
            p_ht = doc.add_paragraph()
            p_ht.alignment = WD_ALIGN_PARAGRAPH.CENTER
            self._set_jp_font(p_ht.add_run("【参考】不動産登記情報（テキストデータ）"), size_pt=14, is_bold=True)
            doc.add_paragraph("※公証人作成用の参考テキストです。\n")
            
            p_txt = doc.add_paragraph(text_data)
            self._set_jp_font(p_txt.runs[0], size_pt=10.5)

        return doc
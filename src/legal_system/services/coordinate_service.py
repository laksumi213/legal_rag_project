import io
from typing import List, Dict, Any, Optional

from src.legal_system.core.database_manager import DatabaseManager
from src.legal_system.utils.pdf_utils import apply_coordinates_to_pdf

class CoordinateService:
    def __init__(self):
        self.db_manager = DatabaseManager()

    def get_coordinates_for_file(self, file_hash: str) -> List[Dict[str, Any]]:
        """
        特定のファイルハッシュに関連する座標データを取得します。
        """
        return self.db_manager.get_coordinates_by_hash(file_hash)

    def get_coordinate_value(self, file_hash: str, label: str) -> Optional[Any]:
        """
        特定のファイルハッシュとラベルに対応する座標の値を直接取得します。
        """
        coords = self.db_manager.get_coordinates_by_hash(file_hash)
        for coord in coords:
            if coord.get("label") == label:
                return coord.get("value")
        return None

    def fill_pdf_with_coordinates(
        self, 
        original_pdf_bytes: bytes, 
        file_hash: str, 
        data: Dict[str, str]
    ) -> io.BytesIO:
        """
        元のPDFとファイルハッシュ、そして埋め込むデータ辞書を受け取り、
        座標を適用したPDFのバイナリデータストリームを返します。動的タグの置換も行います。

        Args:
            original_pdf_bytes (bytes): 元のPDFファイルのバイナリデータ。
            file_hash (str): 座標データに関連付けられたファイルハッシュ。
            data (Dict[str, str]): 埋め込むデータの辞書。キーはタグ名、値は実際のデータ。

        Returns:
            io.BytesIO: 座標が適用され、データが埋め込まれた新しいPDFファイルのバイナリデータストリーム。
        """
        coordinates = self.db_manager.get_coordinates_by_hash(file_hash)

        # 動的タグの置換
        processed_coordinates = []
        for coord in coordinates:
            # 座標辞書をコピーして変更を加える
            temp_coord = coord.copy()
            original_value = str(temp_coord.get("value", ""))

            # RECTタグの場合は置換しない
            if original_value.startswith("RECT:"):
                processed_coordinates.append(temp_coord)
                continue

            # 動的タグの置換ロジック
            for key, value in data.items():
                placeholder = f"{{{key}}}"
                if placeholder in original_value:
                    original_value = original_value.replace(placeholder, str(value))
            temp_coord["value"] = original_value
            processed_coordinates.append(temp_coord)

        # PDFに座標を適用するユーティリティ関数を呼び出す
        return apply_coordinates_to_pdf(original_pdf_bytes, processed_coordinates)

    def ocr_region_with_coordinates(
        self, 
        pdf_bytes: bytes, 
        file_hash: str,
        labels: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """
        PDFバイナリデータとファイルハッシュ、および必要であれば特定のラベルのリストを受け取り、
        登録された矩形座標に基づいてOCRを実行し、結果を辞書で返します。

        Args:
            pdf_bytes (bytes): 元のPDFファイルのバイナリデータ。
            file_hash (str): 座標データに関連付けられたファイルハッシュ。
            labels (Optional[List[str]]): OCRを実行する矩形座標のラベルリスト。Noneの場合はすべての矩形座標を対象。

        Returns:
            Dict[str, str]: OCRで抽出されたテキストの辞書。キーは座標のラベル、値は抽出されたテキスト。
        """
        from src.legal_system.core.ocr_engine import OCREngine # 遅延インポート
        ocr_engine = OCREngine()
        
        if not ocr_engine.is_available:
            return {} # OCRが利用できない場合は空の辞書を返す

        coordinates = self.db_manager.get_coordinates_by_hash(file_hash)
        
        # 矩形座標のみをフィルタリング
        region_coords_to_ocr = []
        for coord in coordinates:
            if str(coord.get("value", "")).startswith("RECT:"):
                if labels is None or coord.get("label") in labels:
                    region_coords_to_ocr.append(coord)

        if not region_coords_to_ocr:
            return {} # 処理すべき矩形座標がない場合は空の辞書を返す

        ocr_results = ocr_engine.process_pdf_region(pdf_bytes, region_coords_to_ocr)

        # 結果をラベルとテキストの辞書に整形
        result_dict = {}
        for coord in region_coords_to_ocr:
            # 抽出されたテキストを対応するラベルに割り当てるロジック
            # 現状、process_pdf_region は座標情報を持たないテキストリストを返すため、
            # どのテキストがどの矩形に対応するかを厳密に紐付けるのは難しい。
            # 一旦、単純に抽出順で割り当てるか、または最初の結果を割り当てる。
            # より高度な実装では、OCR結果のバウンディングボックスと矩形座標を比較して紐付ける。
            # ここでは簡易的に、OCR結果の最初のテキストを対応するラベルに割り当てる。
            if ocr_results:
                # ページと座標が一致するものを探す（簡易版）
                found_text = []
                for ocr_res in ocr_results:
                    if ocr_res.get("page") == coord.get("page"):
                        found_text.append(ocr_res.get("text", ""))

                result_dict[coord.get("label")] = " ".join(found_text).strip()
            else:
                result_dict[coord.get("label")] = ""

        return result_dict
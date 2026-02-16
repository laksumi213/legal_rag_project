# src/services/coordinate_service.py
import io
from typing import Any, Dict, List

from sqlalchemy import select

from database.manager import DatabaseManager
from models.tables import Coordinate
from utils.pdf_utils import apply_coordinates_to_pdf


class CoordinateService:
    def __init__(self):
        self.db_manager = DatabaseManager()

    def get_coordinates_by_hash(self, file_hash: str) -> List[Dict[str, Any]]:
        """
        ファイルハッシュに紐づく座標定義を取得
        """
        with self.db_manager.get_session() as session:
            stmt = select(Coordinate).filter(Coordinate.file_hash == file_hash)
            results = session.execute(stmt).scalars().all()

            return [
                {
                    "id": c.id,
                    "label": c.label,
                    "x": c.x_point,
                    "y": c.y_point,
                    "width": c.width,
                    "height": c.height,
                    "page": c.page_number,
                    "font_size": c.font_size,
                    "color": c.color,
                    "value": c.value,
                    "description": c.description,
                }
                for c in results
            ]

    def fill_pdf_with_data(
        self, original_pdf_bytes: bytes, file_hash: str, data_map: Dict[str, str]
    ) -> io.BytesIO:
        """
        データマッピング(data_map)に基づいてPDFを作成する。
        data_map: {"{client_name}": "山田太郎", ...}
        """
        # 1. 座標定義を取得
        coords = self.get_coordinates_by_hash(file_hash)

        # 2. 値の置換
        processed_coords = []
        for c in coords:
            # コピーを作成
            temp = c.copy()
            original_val = str(temp.get("value", ""))

            # RECTなど特殊タグはそのまま
            if original_val.startswith("RECT:"):
                processed_coords.append(temp)
                continue

            # 置換実行 (例: "{client_name}" -> "山田太郎")
            # 部分一致も含めて置換する
            for key, val in data_map.items():
                if key in original_val:
                    original_val = original_val.replace(key, str(val))

            temp["value"] = original_val
            processed_coords.append(temp)

        # 3. PDF生成
        return apply_coordinates_to_pdf(original_pdf_bytes, processed_coords)

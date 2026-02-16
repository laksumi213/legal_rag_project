import hashlib
import os
import sys

# ルートディレクトリをsys.pathに追加
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import Coordinate, FileRegistry  # 必要に応じて
from services.coordinate_service import CoordinateService
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# -----------------------------------------------------------------------------
# 簡易的なDBセットアップ（テスト用）
# -----------------------------------------------------------------------------
# インメモリSQLiteを使用 (実際のDBを汚染しない)
DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(DATABASE_URL)
Coordinate.metadata.create_all(engine)
FileRegistry.metadata.create_all(engine)

Session = scoped_session(sessionmaker(bind=engine))


# DatabaseManagerをテスト用に再定義またはモック化
class TestDatabaseManager(DatabaseManager):
    def __init__(self):
        self.engine = engine
        self.session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.session_factory)


# -----------------------------------------------------------------------------
# テストデータの準備
# -----------------------------------------------------------------------------
# ダミーPDFバイナリデータ (非常にシンプルな内容)
dummy_pdf_content = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<</ProcSet[/PDF/Text]>>/Contents 4 0 R>>endobj 4 0 obj<</Length 44>>stream\nBT /F1 24 Tf 100 700 Td (Hello World!) Tj ET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000074 00000 n\n0000000121 00000 n\n0000000216 00000 n\ntrailer<</Size 5/Root 1 0 R>>startxref\n303\n%%EOF"

dummy_file_hash = hashlib.md5(dummy_pdf_content).hexdigest()


def setup_dummy_data():
    session = Session()
    try:
        # ファイル登録
        if not session.query(FileRegistry).filter_by(file_hash=dummy_file_hash).first():
            file_reg = FileRegistry(
                file_hash=dummy_file_hash, filename="dummy.pdf", doc_type="test"
            )
            session.add(file_reg)

        # 座標登録
        coords_to_add = [
            {
                "label": "氏名",
                "x": 100.0,
                "y": 700.0,
                "page": 1,
                "font_size": 12,
                "color": "black",
                "value": "{test_name}",
            },
            {
                "label": "住所",
                "x": 100.0,
                "y": 680.0,
                "page": 1,
                "font_size": 10,
                "color": "red",
                "value": "東京都千代田区1-1",
            },
            {
                "label": "矩形フィールド",
                "x": 50.0,
                "y": 600.0,
                "page": 1,
                "font_size": 1,
                "color": "black",
                "value": "RECT:150x50",
            },
        ]
        for coord_data in coords_to_add:
            if (
                not session.query(Coordinate)
                .filter_by(file_hash=dummy_file_hash, label=coord_data["label"])
                .first()
            ):
                coord = Coordinate(file_hash=dummy_file_hash, **coord_data)
                session.add(coord)

        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Dummy data setup failed: {e}")
    finally:
        session.close()


# -----------------------------------------------------------------------------
# テスト実行
# -----------------------------------------------------------------------------
def run_tests():
    print("--- CoordinateService テスト開始 ---")

    # ダミーデータをセットアップ
    setup_dummy_data()

    # CoordinateServiceのインスタンス化 (テスト用DBManagerを渡す)
    service = CoordinateService()
    service.db_manager = TestDatabaseManager()  # テスト用DBManagerを注入

    # 1. get_coordinates_for_file のテスト
    print("\n--- get_coordinates_for_file のテスト ---")
    coords = service.get_coordinates_for_file(dummy_file_hash)
    print(f"取得された座標数: {len(coords)}")
    for c in coords:
        print(f"  - Label: {c['label']}, X: {c['x']}, Y: {c['y']}, Value: {c['value']}")
    assert len(coords) == 3

    # 2. get_coordinate_value のテスト
    print("\n--- get_coordinate_value のテスト ---")
    name_value = service.get_coordinate_value(dummy_file_hash, "氏名")
    print(f"氏名の値: {name_value}")
    assert name_value == "{test_name}"

    rect_value = service.get_coordinate_value(dummy_file_hash, "矩形フィールド")
    print(f"矩形フィールドの値: {rect_value}")
    assert rect_value == "RECT:150x50"

    # 3. fill_pdf_with_coordinates のテスト
    print("\n--- fill_pdf_with_coordinates のテスト ---")
    fill_data = {"test_name": "山田太郎"}
    filled_pdf_stream = service.fill_pdf_with_coordinates(
        dummy_pdf_content, dummy_file_hash, fill_data
    )

    # 生成されたPDFをファイルに保存して確認（手動確認用）
    with open("filled_dummy_test.pdf", "wb") as f:
        f.write(filled_pdf_stream.getvalue())
    print(
        "生成されたPDFを 'filled_dummy_test.pdf' として保存しました。手動で内容を確認してください。"
    )
    assert filled_pdf_stream is not None

    # 4. ocr_region_with_coordinates のテスト (OCRは時間がかかるため、簡易的にAPI呼び出しのみ確認)
    print("\n--- ocr_region_with_coordinates のテスト ---")
    # 実際には OCR でスキャンされたPDFを使用すべきだが、ダミーPDFでシミュレート
    # 矩形座標のラベルを指定してOCRを試行
    # 注意: ダミーPDFのコンテンツがシンプルなので、OCR結果は期待通りにならない可能性があります
    # 実際のテストでは、内容のあるPDFと、それに合わせた座標登録が必要です
    ocr_result = service.ocr_region_with_coordinates(
        dummy_pdf_content, dummy_file_hash, labels=["矩形フィールド"]
    )
    print(f"OCR結果: {ocr_result}")
    # 少なくともエラーなく実行され、辞書が返されることを確認
    assert isinstance(ocr_result, dict)

    print("\n--- CoordinateService テスト完了 ---")


if __name__ == "__main__":
    run_tests()

# src/legal_system/core/data_sync.py

import json

from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import Case, Deceased, Heir


class DataSyncEngine:
    def __init__(self):
        self.db = DatabaseManager()

    def sync_from_kintone_json(self, json_path: str):
        """Bookmarkletから落ちてきたJSONをSQLiteに同期"""
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        session = self.db._get_session()
        try:
            # 1. 案件 (Case) のUpsert
            case_num = data.get("case_number")
            if not case_num:
                return

            case = session.query(Case).filter_by(case_number=case_num).first()
            if not case:
                case = Case(case_number=case_num)
                session.add(case)
                session.flush()  # ID確定

            # 2. 被相続人情報の更新
            d_info = data.get("deceased", {})
            if d_info:
                # 既存があれば取得、なければ作成
                deceased = case.deceased_ref
                if not deceased:
                    deceased = Deceased(case_id=case.case_id)
                    session.add(deceased)

                # 値のセット
                deceased.name_last = d_info.get("name_last", "")
                deceased.name_first = d_info.get("name_first", "")
                # ... 日付変換などは適宜 ...

            # 3. 相続人の更新 (一旦全削除して入れ直すのが安全)
            if "heirs" in data:
                # 既存の相続人を削除
                for h in case.deceased_ref.heirs:
                    session.delete(h)

                # 再登録
                for h_data in data["heirs"]:
                    heir = Heir(
                        deceased_id=case.deceased_ref.id,
                        name_last=h_data.get("name_last", ""),
                        name_first=h_data.get("name_first", ""),
                        relationship_type=h_data.get("relation", ""),
                    )
                    session.add(heir)

            session.commit()
            print(f"✅ Synced Case: {case_num}")

        except Exception as e:
            session.rollback()
            print(f"❌ Sync Error: {e}")
        finally:
            session.close()

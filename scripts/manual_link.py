import json
import sys
from pathlib import Path

# パス設定
root_dir = Path(__file__).resolve().parents[1]
sys.path.append(str(root_dir))

from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import Case, ContactLog, IncomingNoteBuffer


def manual_link_tool():
    db = DatabaseManager()
    session = db._get_session()

    # 1. 保留中のメモを表示
    pendings = session.query(IncomingNoteBuffer).filter_by(status="PENDING").all()

    if not pendings:
        print("\n✅ 現在、保留中（未紐付け）のメモはありません。すべて処理済みです。")
        return

    print(f"\n📋 保留中のメモ一覧 ({len(pendings)}件)")
    print("=" * 60)
    for i, note in enumerate(pendings):
        names = note.detected_names or "[]"
        print(f"ID: {note.id} | 件名: {note.subject}")
        print(f"   -> AI抽出名: {names}")
        print("-" * 60)

    # 2. 操作対象の選択
    target_id_str = input(
        "\n修正・紐付けしたいメモの「ID」を入力してください (終了はEnter): "
    )
    if not target_id_str:
        return

    target_note = session.query(IncomingNoteBuffer).get(int(target_id_str))
    if not target_note:
        print("❌ 指定されたIDのメモが見つかりません。")
        return

    # 3. 正しい名前の入力
    print(f"\n対象: {target_note.subject}")
    correct_name = input(
        "紐付けたい案件の「顧客名（氏名）」を入力してください (例: 冨田 総子): "
    ).strip()

    if not correct_name:
        print("キャンセルしました。")
        return

    # 4. 案件検索 & 強制紐付け
    # スペースを無視して検索
    clean_target = correct_name.replace(" ", "").replace("　", "")

    # 案件テーブルから検索
    cases = session.query(Case).all()
    target_case = None

    for c in cases:
        c_name = (c.client_name or "").replace(" ", "").replace("　", "")
        if clean_target in c_name:  # 部分一致でもヒットさせる
            target_case = c
            break

    if target_case:
        print(
            f"\n✅ 案件が見つかりました: 【{target_case.case_number}】 {target_case.client_name}"
        )
        confirm = input("この案件に紐付けますか？ (y/n): ")

        if confirm.lower() == "y":
            # A. 抽出名を書き換える（履歴のため）
            target_note.detected_names = json.dumps(
                [target_case.client_name], ensure_ascii=False
            )

            # B. ContactLogに保存
            new_log = ContactLog(
                case_id=target_case.case_id,
                contact_content=target_note.body_text,
                is_thank_you_payment=False,
            )
            session.add(new_log)

            # C. ステータス更新
            target_note.status = "LINKED"
            target_note.linked_case_id = target_case.case_id

            session.commit()
            print(
                f"\n🎉 完了！ メモを「{target_case.client_name}」様の履歴に追加しました。"
            )
    else:
        print(
            f"\n❌ 「{correct_name}」に一致する案件がデータベースに見つかりませんでした。"
        )
        print("先にブラウザで案件を登録してください。")

    session.close()


if __name__ == "__main__":
    manual_link_tool()

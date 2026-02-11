# tests/test_task_service.py

"""
タスク管理機能のテストコード

日付: 2026-02-12
使用方法:
    python tests/test_task_service.py
"""

import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
root_dir = Path(__file__).resolve().parents[1]
sys.path.append(str(root_dir))

from src.services.task_service import TaskService
from src.legal_system.core.database_manager import DatabaseManager
from src.legal_system.models.tables import Case, TaskTemplate
from datetime import date


def test_task_initialization():
    """タスク初期化のテスト"""
    print("\n" + "=" * 60)
    print("タスク初期化テスト")
    print("=" * 60)
    
    task_service = TaskService()
    db = DatabaseManager()
    session = db._get_session()
    
    try:
        # テストケースを取得（最初の案件）
        case = session.query(Case).first()
        
        if not case:
            print("❌ テスト用の案件が見つかりません。")
            print("   先に案件を作成してください。")
            return False
        
        print(f"📋 テスト対象案件: {case.case_number} - {case.client_name}")
        
        # タスクテンプレートの確認
        templates = session.query(TaskTemplate).all()
        print(f"📝 登録済みテンプレート数: {len(templates)}件")
        
        if not templates:
            print("❌ タスクテンプレートが登録されていません。")
            print("   先に python scripts/seed_data.py を実行してください。")
            return False
        
        # タスク初期化を実行
        print(f"\n🚀 案件 {case.case_id} にタスクを初期化します...")
        success = task_service.initialize_tasks(case.case_id)
        
        if success:
            print("✅ タスク初期化成功！")
            
            # 初期化されたタスクを確認
            tasks = task_service.get_tasks_by_case(case.case_id)
            print(f"\n📊 生成されたタスク数: {len(tasks)}件")
            
            print("\n【生成されたタスク一覧】")
            for i, task in enumerate(tasks, 1):
                status = "✅" if task["is_completed"] else "⬜"
                print(f"{i}. {status} {task['description']}")
                print(f"   期限: {task['due_date']}, 担当: {task['assigned_user_name']}, 重み: {task['weight']}")
            
            return True
        else:
            print("❌ タスク初期化失敗")
            return False
    
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()


def test_task_update():
    """タスク更新のテスト"""
    print("\n" + "=" * 60)
    print("タスク更新テスト")
    print("=" * 60)
    
    task_service = TaskService()
    db = DatabaseManager()
    session = db._get_session()
    
    try:
        # テストケースを取得
        case = session.query(Case).first()
        
        if not case:
            print("❌ テスト用の案件が見つかりません。")
            return False
        
        # タスクを取得
        tasks = task_service.get_tasks_by_case(case.case_id)
        
        if not tasks:
            print("❌ タスクが存在しません。先にタスク初期化テストを実行してください。")
            return False
        
        print(f"📋 案件 {case.case_number} のタスクを更新します...")
        
        # 最初のタスクを完了状態に更新
        first_task = tasks[0]
        print(f"\n🔄 タスク「{first_task['description']}」を完了状態に更新...")
        
        updates = [
            {
                "task_id": first_task["task_id"],
                "is_completed": True,
                "due_date": date.today()
            }
        ]
        
        success = task_service.update_tasks_bulk(updates)
        
        if success:
            print("✅ タスク更新成功！")
            
            # 更新後のタスクを確認
            updated_tasks = task_service.get_tasks_by_case(case.case_id)
            updated_task = next(t for t in updated_tasks if t["task_id"] == first_task["task_id"])
            
            print(f"\n【更新後の状態】")
            print(f"完了状態: {updated_task['is_completed']}")
            print(f"期限日: {updated_task['due_date']}")
            
            return True
        else:
            print("❌ タスク更新失敗")
            return False
    
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()


def test_custom_task_addition():
    """カスタムタスク追加のテスト"""
    print("\n" + "=" * 60)
    print("カスタムタスク追加テスト")
    print("=" * 60)
    
    task_service = TaskService()
    db = DatabaseManager()
    session = db._get_session()
    
    try:
        # テストケースを取得
        case = session.query(Case).first()
        
        if not case:
            print("❌ テスト用の案件が見つかりません。")
            return False
        
        print(f"📋 案件 {case.case_number} にカスタムタスクを追加します...")
        
        # カスタムタスクを追加
        success = task_service.add_custom_task(
            case_id=case.case_id,
            description="【テスト】特別な書類の作成",
            due_date=date.today(),
            assigned_user_id=case.operator_id,
            weight=1.5
        )
        
        if success:
            print("✅ カスタムタスク追加成功！")
            
            # 追加されたタスクを確認
            tasks = task_service.get_tasks_by_case(case.case_id)
            custom_task = next(
                (t for t in tasks if "【テスト】" in t["description"]),
                None
            )
            
            if custom_task:
                print(f"\n【追加されたタスク】")
                print(f"タスク名: {custom_task['description']}")
                print(f"期限日: {custom_task['due_date']}")
                print(f"担当者: {custom_task['assigned_user_name']}")
                print(f"重み: {custom_task['weight']}")
            
            return True
        else:
            print("❌ カスタムタスク追加失敗")
            return False
    
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()


def run_all_tests():
    """全テストを実行"""
    print("\n" + "=" * 60)
    print("タスク管理機能 統合テスト")
    print("日付: 2026-02-12")
    print("=" * 60)
    
    results = []
    
    # テスト1: タスク初期化
    results.append(("タスク初期化", test_task_initialization()))
    
    # テスト2: タスク更新
    results.append(("タスク更新", test_task_update()))
    
    # テスト3: カスタムタスク追加
    results.append(("カスタムタスク追加", test_custom_task_addition()))
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("テスト結果サマリー")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ 成功" if result else "❌ 失敗"
        print(f"{test_name}: {status}")
    
    total_tests = len(results)
    passed_tests = sum(1 for _, result in results if result)
    
    print(f"\n合計: {passed_tests}/{total_tests} テスト成功")
    
    if passed_tests == total_tests:
        print("\n🎉 全テスト成功！タスク管理機能は正常に動作しています。")
    else:
        print("\n⚠️ 一部のテストが失敗しました。ログを確認してください。")


if __name__ == "__main__":
    run_all_tests()

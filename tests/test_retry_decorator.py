"""
リトライデコレータの動作確認テスト

使用方法:
    python tests/test_retry_decorator.py
"""

import logging
import os
import sys

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils.retry_decorator import retry_with_backoff

# ロガー設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TestException(Exception):
    """テスト用の例外"""

    pass


# テスト1: 正常系（1回目で成功）
@retry_with_backoff(max_retries=3, exceptions=(TestException,))
def test_success_on_first_try():
    """1回目で成功するケース"""
    logger.info("✅ 成功しました")
    return "SUCCESS"


# テスト2: 2回失敗後、3回目で成功
call_count = 0


@retry_with_backoff(max_retries=3, backoff_factor=1.0, exceptions=(TestException,))
def test_success_on_third_try():
    """2回失敗後、3回目で成功するケース"""
    global call_count
    call_count += 1

    if call_count < 3:
        logger.info(f"❌ 失敗 (試行 {call_count}/3)")
        raise TestException(f"意図的な失敗 (試行 {call_count})")

    logger.info(f"✅ 成功しました (試行 {call_count}/3)")
    return "SUCCESS_AFTER_RETRIES"


# テスト3: すべて失敗（例外が再送出される）
@retry_with_backoff(max_retries=3, backoff_factor=1.0, exceptions=(TestException,))
def test_all_failures():
    """すべて失敗するケース"""
    logger.info("❌ 失敗しました")
    raise TestException("すべての試行で失敗")


def run_tests():
    """テストを実行"""
    print("=" * 60)
    print("リトライデコレータ 動作確認テスト")
    print("=" * 60)

    # テスト1: 正常系
    print("\n【テスト1】1回目で成功")
    print("-" * 60)
    try:
        result = test_success_on_first_try()
        print(f"結果: {result}")
        print("✅ テスト1 成功\n")
    except Exception as e:
        print(f"❌ テスト1 失敗: {e}\n")

    # テスト2: リトライ後に成功
    print("\n【テスト2】2回失敗後、3回目で成功")
    print("-" * 60)
    global call_count
    call_count = 0  # カウンターリセット
    try:
        result = test_success_on_third_try()
        print(f"結果: {result}")
        print("✅ テスト2 成功\n")
    except Exception as e:
        print(f"❌ テスト2 失敗: {e}\n")

    # テスト3: すべて失敗
    print("\n【テスト3】すべて失敗（例外が再送出される）")
    print("-" * 60)
    try:
        result = test_all_failures()
        print("❌ テスト3 失敗: 例外が発生しませんでした")
    except TestException as e:
        print("✅ テスト3 成功: 期待通り例外が再送出されました")
        print(f"   例外メッセージ: {e}\n")

    print("=" * 60)
    print("テスト完了")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()

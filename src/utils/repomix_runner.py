# src/utils/repomix_runner.py
import logging
import subprocess

from core.config import Config

logger = logging.getLogger(__name__)


def run_repomix_sync() -> bool:
    """
    ソースコードを集約して repomix-output.md を生成します。
    同期実行用（asyncio.to_thread で呼び出すことを想定）
    """
    logger.info("🚀 ソースコードの集約を開始します...")

    # プロジェクトルートで実行するためのパス解決
    # src/utils/repomix_runner.py -> src -> root
    cwd = Config.BASE_DIR

    command = "npx -y repomix --style markdown"

    try:
        # shell=True は Windows/Mac 両対応のため使用
        result = subprocess.run(
            command, shell=True, check=True, cwd=cwd, capture_output=True, text=True
        )
        logger.info("✅ ソースコードの集約が完了しました")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Repomix実行失敗: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"❌ 予期せぬエラー: {e}")
        return False

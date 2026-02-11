"""
統一エラーハンドリング＆リトライ機構

外部API呼び出しに対する指数バックオフ付きリトライデコレータを提供します。
"""

from functools import wraps
import time
import logging
from typing import Callable, Tuple, Type

logger = logging.getLogger(__name__)


def retry_with_backoff(
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    log_to_audit: bool = False
):
    """
    指数バックオフ付きリトライデコレータ
    
    Args:
        max_retries: 最大リトライ回数（デフォルト: 3回）
        backoff_factor: バックオフ係数（デフォルト: 2.0）
        exceptions: キャッチする例外のタプル
        log_to_audit: AuditLogへの記録を有効化（デフォルト: False）
    
    使用例:
        @retry_with_backoff(max_retries=3, exceptions=(requests.RequestException,))
        def fetch_data():
            return requests.get("https://api.example.com")
    
    リトライ動作:
        - 1回目の失敗: 2秒待機後リトライ
        - 2回目の失敗: 4秒待機後リトライ
        - 3回目の失敗: 例外を再送出
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    is_last_attempt = (attempt == max_retries - 1)
                    
                    if is_last_attempt:
                        logger.error(
                            f"❌ {func.__name__} failed after {max_retries} attempts: {e}",
                            exc_info=True
                        )
                        
                        # AuditLogへの記録（オプション）
                        if log_to_audit:
                            _log_to_audit_table(func.__name__, str(e), args, kwargs)
                        
                        raise  # 最終試行で失敗したら例外を再送出
                    
                    # リトライ待機時間の計算（指数バックオフ）
                    wait_time = backoff_factor ** attempt
                    logger.warning(
                        f"⚠️ {func.__name__} failed (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {wait_time:.1f}s... Error: {e}"
                    )
                    time.sleep(wait_time)
            
        return wrapper
    return decorator


def _log_to_audit_table(func_name: str, error_msg: str, args, kwargs):
    """AuditLogテーブルへエラーを記録（オプション機能）"""
    try:
        from legal_system.core.database_manager import DatabaseManager
        from legal_system.models.tables import AuditLog
        from datetime import datetime
        
        db = DatabaseManager()
        session = db._get_session()
        
        # 引数情報を安全に文字列化（機密情報を含む可能性があるため、長さを制限）
        args_str = str(args)[:500] if args else ""
        kwargs_str = str(kwargs)[:500] if kwargs else ""
        
        log_entry = AuditLog(
            action_type="RETRY_FAILURE",
            target=func_name,
            details=f"Error: {error_msg}\nArgs: {args_str}\nKwargs: {kwargs_str}",
            timestamp=datetime.now()
        )
        session.add(log_entry)
        session.commit()
        session.close()
        logger.info(f"✅ Logged retry failure to AuditLog: {func_name}")
    except Exception as e:
        logger.error(f"Failed to log to AuditLog: {e}")

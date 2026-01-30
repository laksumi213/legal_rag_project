# src/utils/date_utils.py
import datetime
import re

def parse_all_flexible_date(date_obj: object) -> datetime.date:
    """
    様々な形式の日付データ（文字列または日付オブジェクト）を datetime.date に変換する。
    対応形式: YYYY-MM-DD, YYYY/MM/DD, 和暦, datetime.date, datetime.datetime
    """
    if date_obj is None:
        return None
    
    # 既に date 型ならそのまま返す
    if isinstance(date_obj, datetime.date):
        return date_obj
    
    # datetime 型なら date に変換
    if isinstance(date_obj, datetime.datetime):
        return date_obj.date()

    # 文字列でない場合は None (安全策)
    if not isinstance(date_obj, str):
        return None
    
    s = date_obj.strip()
    if not s:
        return None

    # 1. YYYY-MM-DD / YYYY/MM/DD
    try:
        s = s.replace('/', '-')
        return datetime.datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        pass

    # 2. YYYY年MM月DD日
    try:
        return datetime.datetime.strptime(s, "%Y年%m月%d日").date()
    except ValueError:
        pass

    # 3. 数字8桁 (20250101)
    if s.isdigit() and len(s) == 8:
        try:
            return datetime.datetime.strptime(s, "%Y%m%d").date()
        except ValueError:
            pass

    # 必要であれば和暦変換ロジックを追加
    return None

def convert_seireki_to_wareki(dt: datetime.date) -> str:
    """西暦Dateを和暦文字列に変換"""
    if not dt: return ""
    if dt.year >= 2019:
        n = dt.year - 2018
        gengo = "令和"
    elif dt.year >= 1989:
        n = dt.year - 1988
        gengo = "平成"
    elif dt.year >= 1926:
        n = dt.year - 1925
        gengo = "昭和"
    else:
        n = dt.year - 1911
        gengo = "大正"
    
    nen = "元" if n == 1 else str(n)
    return f"{gengo}{nen}年{dt.month}月{dt.day}日"
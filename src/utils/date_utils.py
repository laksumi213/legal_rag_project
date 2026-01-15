# src/utils/date_utils.py
import datetime
import re

def parse_all_flexible_date(date_str: str) -> datetime.date:
    """
    様々な形式の日付文字列を datetime.date に変換する。
    対応形式: YYYY-MM-DD, YYYY/MM/DD, YYYY年MM月DD日, 和暦など
    """
    if not date_str:
        return None
    
    s = date_str.strip()
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
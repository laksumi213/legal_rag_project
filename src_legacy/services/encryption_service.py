# src/services/encryption_service.py
import os
import subprocess
import logging
from typing import List
from pathlib import Path

# ロガーの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EncryptionService:
    """
    同梱した7-Zipバイナリ(7za.exe)を使用して暗号化を行うサービスクラス。
    Windows標準機能(エクスプローラー)で解凍可能な ZipCrypto 方式を採用します。
    """

    # src/services/encryption_service.py から見て ../utils/7za.exe を指す
    # 実行環境に合わせて絶対パスに変換
    BASE_DIR = Path(__file__).resolve().parent.parent # srcディレクトリ
    EXE_PATH = str(BASE_DIR / "utils" / "7za.exe")

    @staticmethod
    def create_encrypted_zip(file_paths: List[str], output_path: str, password: str) -> None:
        """
        7-Zipを使用して、Windows標準機能で解凍可能なパスワード付きZIPを作成します。

        Args:
            file_paths (List[str]): 圧縮するファイルのフルパスリスト
            output_path (str): 出力するZIPファイルのパス
            password (str): 設定するパスワード
        """
        if not file_paths or not password:
            raise ValueError("ファイルとパスワードが必要です。")

        # バイナリの存在確認
        if not os.path.exists(EncryptionService.EXE_PATH):
            logger.error(f"7za.exe not found at: {EncryptionService.EXE_PATH}")
            raise FileNotFoundError(
                f"暗号化エンジン(7za.exe)が見つかりません。以下の場所に配置してください:\n{EncryptionService.EXE_PATH}"
            )

        try:
            # 既存の出力ファイルがある場合は削除（7zはデフォルトで追記モードのため）
            if os.path.exists(output_path):
                os.remove(output_path)

            # 7-Zipコマンドの構築
            # a: 追加(圧縮)
            # -tzip: ZIP形式を指定
            # -p: パスワードを指定
            # -mem=ZipCrypto: Windowsエクスプローラー互換の暗号化方式を指定 (重要)
            cmd = [
                EncryptionService.EXE_PATH,
                "a",
                "-tzip",
                f"-p{password}",
                "-mem=ZipCrypto",
                output_path
            ]
            
            # 圧縮対象ファイルの追加
            cmd.extend(file_paths)

            # コマンドの実行 (Windows特有のコンソールウィンドウ非表示設定を含む)
            creationflags = 0
            if os.name == 'nt':
                creationflags = subprocess.CREATE_NO_WINDOW

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                creationflags=creationflags
            )
            
            logger.info(f"Encrypted ZIP created successfully: {output_path}")

        except subprocess.CalledProcessError as e:
            logger.error(f"7-Zip Error: {e.stderr}")
            raise RuntimeError(f"ZIP作成に失敗しました。\n詳細: {e.stderr}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise RuntimeError(f"予期せぬエラーが発生しました: {str(e)}")
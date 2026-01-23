import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# 許可する権限の範囲（読み取り専用）
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def generate_token():
    creds = None
    # すでに token.json がある場合はロード（再生成時など）
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # 有効なトークンがない場合、新規取得
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 トークンをリフレッシュします...")
            creds.refresh(Request())
        else:
            print("🚀 ブラウザを起動して認証を行います...")
            
            if not os.path.exists('credentials.json'):
                print("❌ エラー: credentials.json が見つかりません。ルートディレクトリに配置してください。")
                return

            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            
            # ここでローカルサーバーを立ち上げ、ブラウザ認証を行う
            creds = flow.run_local_server(port=0)
        
        # token.json として保存
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            print("✅ 成功: token.json を生成しました！")

if __name__ == '__main__':
    generate_token()
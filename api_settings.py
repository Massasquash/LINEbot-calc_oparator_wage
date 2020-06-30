import os
from oauth2client.service_account import ServiceAccountCredentials

from linebot import LineBotApi, WebhookHandler

# Google Drive APIの認証を実行
def set_google_credentials():
  scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
  credential_dict = {
    "type": "service_account",
    "project_id": os.environ['SHEET_PROJECT_ID'],
    "private_key_id": os.environ['SHEET_PRIVATE_KEY_ID'],
    "private_key": os.environ['SHEET_PRIVATE_KEY'],
    "client_email": os.environ['SHEET_CLIENT_EMAIL'],
    "client_id": os.environ['SHEET_CLIENT_ID'],
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": os.environ['SHEET_CLIENT_X509_CERT_URL']
  }

  credentials = ServiceAccountCredentials.from_json_keyfile_dict(credential_dict, scope)
  return credentials


# LINE messaging APIの設定
#TODO:本番環境への移行時はDEVのついていない環境変数を使用する
line_bot_api = LineBotApi(os.environ["LINE_CHANNEL_ACCESS_TOKEN"])
handler = WebhookHandler(os.environ["LINE_CHANNEL_SECRET"])
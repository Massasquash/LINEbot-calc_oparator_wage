from flask import Flask, request, abort
import os, gspread

from linebot import (
    LineBotApi, WebhookHandler,
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, StickerSendMessage,
)
from linebot.exceptions import InvalidSignatureError

from oauth2client.service_account import ServiceAccountCredentials


# Google Drive APIの認証
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

gc = gspread.authorize(credentials)

spreadsheet = os.environ['SPREADSHEET_KEY']
worksheet = gc.open_by_key(spreadsheet).sheet1

# LINEbotの認証
channel_secret = os.environ["LINE_CHANNEL_SECRET"]
channel_access_token = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]

# flaskアプリ実装
app = Flask(__name__)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

@app.route('/')
def hello_world():
    return 'hello world!'

@app.route('/callback', methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info('Request body: ' + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# メッセージ応答メソッド
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.message.type == 'text':
        # スプレッドシートのA列に新しい行で追加
        text = event.message.text
        worksheet.append_row([text])

        msg = f' [{text}]をシートに登録しました'
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg)
        )

#-----------------
if __name__ == '__main__':
    app.run()
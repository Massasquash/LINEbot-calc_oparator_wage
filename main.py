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
filename = 'gcp_credentials.json'
scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name(filename, scope)

gc = gspread.authorize(credentials)

SPREADSHEET_KEY = '1OqyYfjv7cLs4SNd-c3yfD0E2ibvBkvyAviqw6P1CnOU'
worksheet = gc.open_by_key(SPREADSHEET_KEY).sheet1

# LINEbotの認証
channel_secret = os.environ["CHANNEL_SECRET"]
channel_access_token = os.environ["CHANNEL_ACCESS_TOKEN"]

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
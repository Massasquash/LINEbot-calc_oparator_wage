from flask import Flask, request, abort
import os, gspread

from linebot import (
    LineBotApi, WebhookHandler,
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, StickerSendMessage,
)
from linebot.exceptions import InvalidSignatureError

import api_settings

#LINE botの設定
line_bot_api = LineBotApi(os.environ["LINE_CHANNEL_ACCESS_TOKEN"])
handler = WebhookHandler(os.environ["LINE_CHANNEL_SECRET"])

# Spreadsheet連携
credentials = api_settings.set_google_credentials()
gc = gspread.authorize(credentials)
spreadsheet = os.environ['SPREADSHEET_KEY']
worksheet = gc.open_by_key(spreadsheet).sheet1

# flaskアプリ実装（初期化）
app = Flask(__name__)

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
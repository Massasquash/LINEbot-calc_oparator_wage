from flask import Flask, request, abort
import os, gspread

from linebot import LineBotApi, WebhookHandler
from linebot.models import (
    TemplateSendMessage, ButtonsTemplate,
    PostbackAction, MessageAction,
    DatetimePickerAction, QuickReply, QuickReplyButton,
    MessageEvent, TextMessage, TextSendMessage
)
from linebot.exceptions import InvalidSignatureError

import api_settings
import tools

#LINE botの設定
line_bot_api = LineBotApi(os.environ["LINE_CHANNEL_ACCESS_TOKEN"])
handler = WebhookHandler(os.environ["LINE_CHANNEL_SECRET"])

# Spreadsheet連携
credentials = api_settings.set_google_credentials()
gc = gspread.authorize(credentials)
ss_key = os.environ['SPREADSHEET_KEY']

ss = gc.open_by_key(ss_key)
record_sheet = ss.worksheet('record')
master_sheet = ss.worksheet('master')

# マスター情報の取得
machines, persons = tools.get_master_data()

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
        text = event.message.text

        if text == "日報入力":
            datetime_picker = TemplateSendMessage(
                alt_text='作業開始時間を入力',
                template=ButtonsTemplate(
                    text='開始時間を入れてください',
                    title='作業日報',
                    actions=[
                        DatetimePickerAction(
                            label='入力',
                            data='action=setstarttime',
                            mode='datetime',
                        )
                    ]
                )
            )

            line_bot_api.reply_message(
                event.reply_token,
                datetime_picker
            )
            return
        
        elif text == "リプライ":
            def make_quickreply_item(obj):
                item = QuickReplyButton(
                    action = PostbackAction(label=obj[0], data=f'action=quickreply-data1'))
                return item
                
            quick_reply_message = TextSendMessage(
                text = '選んでください。',
                quick_reply = QuickReply(
                    items = map(make_quickreply_item, machines)
                )
            )

            line_bot_api.reply_message(
                event.reply_token,
                quick_reply_message
            )
            return


        # スプレッドシートのA列に新しい行で追加
        # text = event.message.text
        # worksheet.append_row([text])

        # msg = f' [{text}]をシートに登録しました'
        # msg = event.message.text
        # line_bot_api.reply_message(
        #     event.reply_token,
        #     TextSendMessage(text=msg)
        # )

#-----------------
if __name__ == '__main__':
    app.run()
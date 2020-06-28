from flask import Flask, request, abort
import os
from datetime import datetime as dt
import gspread

from linebot import LineBotApi, WebhookHandler
from linebot.models import (
    TemplateSendMessage, ButtonsTemplate,
    PostbackAction, MessageAction,
    DatetimePickerAction, QuickReply, QuickReplyButton,
    MessageEvent, PostbackEvent,
    TextMessage, TextSendMessage,
)
from linebot.exceptions import InvalidSignatureError

import api_settings, tools, actions

#LINE botの設定
#TODO:本番環境への移行時はDEVのついていない環境変数を使用する
line_bot_api = LineBotApi(os.environ["DEV_LINE_CHANNEL_ACCESS_TOKEN"])
handler = WebhookHandler(os.environ["DEV_LINE_CHANNEL_SECRET"])

# Spreadsheet連携
credentials = api_settings.set_google_credentials()
gc = gspread.authorize(credentials)
ss_key = os.environ['SPREADSHEET_KEY']

ss = gc.open_by_key(ss_key)
record_sheet = ss.worksheet('record')
master_sheet = ss.worksheet('master')
cache_sheet = ss.worksheet('cache')

# マスター情報の取得
machines, persons = tools.get_master_data()

# flaskアプリ実装（初期化）
app = Flask(__name__)

# flaskのルート設定
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
    print(tools.get_user_sheet(event))
    if event.message.type == 'text':
        ev_text = event.message.text
        if ev_text == '日報入力':
            actions.send_start_datetime_picker(event)
        if ev_text == '集計':
            msg_times_per_day, msg_total_wages = tools.calc_operator_wages()
            print(len(msg_times_per_day))
            print(len(msg_total_wages))
            actions.reply_two_texts(event, msg_times_per_day, msg_total_wages)

#ポストバックアクション応答メソッド
@handler.add(PostbackEvent)
def handle_postback(event):
    ev_data = event.postback.data

    if ev_data == 'starttime': 
        starttime = event.postback.params['datetime']
        cache_sheet.update_acell('B2', starttime)
        actions.send_end_datetime_picker(event)

    if ev_data == 'endtime':
        endtime = event.postback.params['datetime']
        cache = cache_sheet.get('B1:B5')
        starttime = dt.strptime(cache[1][0], '%Y-%m-%dT%H:%M')
        if starttime >= dt.strptime(endtime, '%Y-%m-%dT%H:%M'):
            actions.reply_text(event, 'もう一度、終了時間を入力してください\n（終了時間は開始時間より後に設定してください）')
            return
        cache_sheet.update_acell('B3', endtime)
        actions.send_machines_quickreply(event, machines)

    if ev_data.startswith('machine'):
        machine = ev_data.split("'")[1]
        cache_sheet.update_acell('B4', machine)
        actions.send_persons_quickreply(event, persons)
    
    if ev_data.startswith('person'):
        person = ev_data.split("'")[1]
        cache_sheet.update_acell('B5', person)  
        msg = tools.create_confirm_message()
        actions.send_entry_quickreply(event, msg)

    if ev_data.startswith('entry'):
        if ev_data[-1] == '0':
            cache = cache_sheet.get('B1:B6')
            record_sheet.append_row([cache[1][0], cache[2][0], cache[3][0], cache[4][0], cache[5][0]])
            msg = '日報を登録しました！'
            actions.reply_text(event, msg)
        elif ev_data[-1] == '1':
            msg = 'キャンセルしました。もう一度最初から入力してください。'
            actions.reply_text(event, msg)

#-----------------
if __name__ == '__main__':
    app.run()
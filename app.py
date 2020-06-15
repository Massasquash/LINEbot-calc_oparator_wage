from flask import Flask, request, abort
import os, gspread

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

# TODO:あとで修正
cache_sheet = ss.worksheet('cache')

# flaskアプリ実装（初期化）
app = Flask(__name__)

# flaskのルート設定
@app.route('/')
def hello_world():
    print(cache)
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
        ev_text = event.message.text
        if ev_text == '日報入力':
            actions.send_start_datetime_picker(event)
            return
        if ev_text == '集計':
            reply_text(event, 'これから作ります')
        
#ポストバックアクション応答メソッド
@handler.add(PostbackEvent)
def handle_postback(event):
    ev_data = event.postback.data

    if ev_data == 'starttime':
        starttime = event.postback.params['datetime']
        cache_sheet.update_acell('B2', starttime)
        # actions.reply_text(event, f'開始時間は{starttime}')
        actions.send_end_datetime_picker(event)
        return

    if ev_data == 'endtime':
        endtime = event.postback.params['datetime']
        cache_sheet.update_acell('B3', endtime)
        actions.send_machines_quickreply(event, machines)
        return

    if ev_data.startswith('machine'):
        machine = ev_data.split("'")[1]
        cache_sheet.update_acell('B4', machine)
        actions.send_persons_quickreply(event, persons)
        return
    
    if ev_data.startswith('person'):
        person = ev_data.split("'")[1]
        cache_sheet.update_acell('B5', person)
        cache = cache_sheet.get('B1:B5')
        
        msg = f'''
        作業開始：{cache[1][0]}\n\
        作業終了：{cache[2][0]}\n\
        コンバイン名：{cache[3][0]}\n\
        作業者名：{cache[4][0]}\n\n\
        この日報を登録しますか？
        '''

        actions.send_entry_quickreply(event, msg)
        return

    if ev_data.startswith('entry'):
        if ev_data[-1] == '0':
            cache = cache_sheet.get('B1:B5')
            record_sheet.append_row([cache[1][0], cache[2][0], cache[3][0], cache[4][0]])
            msg = '日報を登録しました！'
            actions.reply_text(event, msg)
            return
        elif ev_data[-1] == '1':
            msg = 'キャンセルしました。最初から入力してください。'
            actions.reply_text(event, msg)
            return

#-----------------
if __name__ == '__main__':
    app.run()
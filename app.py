from flask import Flask, request, abort
from datetime import datetime as dt
import os
import gspread

from linebot.models import MessageEvent, TextMessage, PostbackEvent
from linebot.exceptions import InvalidSignatureError

import api_settings, tools, actions

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
        api_settings.handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# メッセージ応答メソッド
@api_settings.handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.message.type == 'text':
        ev_text = event.message.text
        if ev_text == '日報入力':
            actions.send_start_datetime_picker(event)
        elif ev_text == '確認':
            msg_times_per_day, msg_total_wages = tools.calc_operator_wages()
            actions.reply_text(event, msg_times_per_day)
        elif ev_text == '集計':
            msg_times_per_day, msg_total_wages = tools.calc_operator_wages()
            actions.reply_text(event, msg_total_wages)

#ポストバックアクション応答メソッド
@api_settings.handler.add(PostbackEvent)
def handle_postback(event):
    ev_data = event.postback.data
    user_cache_sheet = tools.get_user_sheet(event)
    cache = user_cache_sheet.get('B1:B5')
    print(event)
    if ev_data == 'starttime': 
        starttime = event.postback.params['datetime']
        user_cache_sheet.update_acell('B1', starttime)
        actions.send_end_datetime_picker(event)

    if ev_data == 'endtime':
        endtime = event.postback.params['datetime']
        starttime = dt.strptime(cache[0][0], '%Y-%m-%dT%H:%M')
        if starttime >= dt.strptime(endtime, '%Y-%m-%dT%H:%M'):
            actions.reply_text(event, 'もう一度、終了時間を入力してください\n（終了時間は開始時間より後に設定してください）')
            return
        user_cache_sheet.update_acell('B2', endtime)
        actions.send_machines_quickreply(event, tools.machines)

    if ev_data.startswith('machine'):
        machine = ev_data.split("'")[1]
        user_cache_sheet.update_acell('B3', machine)
        actions.send_persons_quickreply(event, tools.persons)
    
    if ev_data.startswith('person'):
        person = ev_data.split("'")[1]
        user_cache_sheet.update_acell('B4', person)  
        msg = tools.create_confirm_message(event)
        actions.send_entry_quickreply(event, msg)

    if ev_data.startswith('entry'):
        if ev_data[-1] == '0':
            tools.save_records(user_cache_sheet)
            msg = '日報を登録しました！'
            actions.reply_text(event, msg)
        elif ev_data[-1] == '1':
            msg = 'キャンセルしました。もう一度最初から入力してください。'
            actions.reply_text(event, msg)

#-----------------
if __name__ == '__main__':
    app.run()
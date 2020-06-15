import os

from linebot import LineBotApi, WebhookHandler
from linebot.models import (
    TemplateSendMessage, ButtonsTemplate,
    PostbackAction, MessageAction,
    DatetimePickerAction, QuickReply, QuickReplyButton,
    MessageEvent, PostbackEvent,
    TextMessage, TextSendMessage,
)

import app

def reply_text(event, msg):
    app.line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=msg)
    )

def send_start_datetime_picker(event):
    datetime_picker = TemplateSendMessage(
        alt_text='作業開始時間を入力',
        template=ButtonsTemplate(
            text='開始時間を入れてください',
            title='作業日報',
            actions=[
                DatetimePickerAction(
                    label='入力',
                    data='starttime',
                    mode='datetime',
                )
            ]
        )
    )
    app.line_bot_api.reply_message(
        event.reply_token,
        datetime_picker
    )
    return

def send_end_datetime_picker(event):
    datetime_picker = TemplateSendMessage(
        alt_text='作業終了時間を入力',
        template=ButtonsTemplate(
            text=f'終了時間を入れてください',
            title='作業日報',
            actions=[
                DatetimePickerAction(
                    label='入力',
                    data='endtime',
                    mode='datetime',
                )
            ]
        )
    )
    app.line_bot_api.reply_message(
        event.reply_token,
        datetime_picker
    )
    return



def send_machines_quickreply(event, obj):
    def make_quickreply_item(obj):
        item = QuickReplyButton(
            action = PostbackAction(label=obj[0], data=f'machine={obj}')
        )
        return item

    quick_reply_message = TextSendMessage(
        text = 'コンバイン選択',
        quick_reply = QuickReply(
            items = map(make_quickreply_item, obj)
        )
    )
    app.line_bot_api.reply_message(
        event.reply_token,
        quick_reply_message
    )
    return

def send_persons_quickreply(event, obj):
    def make_quickreply_item(obj):
        item = QuickReplyButton(
            action = PostbackAction(label=obj[0], data=f'person={obj}')
        )
        return item

    quick_reply_message = TextSendMessage(
        text = '作業者を選択',
        quick_reply = QuickReply(items = map(make_quickreply_item, obj))
    )
    app.line_bot_api.reply_message(
        event.reply_token,
        quick_reply_message
    )
    return


def send_entry_quickreply(event, msg):
    items =[
        QuickReplyButton(
            action = PostbackAction(label='はい', data='entry-0')
        ),
        QuickReplyButton(
            action = PostbackAction(label='いいえ', data='entry-1')
        ),
    ]

    quick_reply_message = TextSendMessage(
        text = msg,
        quick_reply = QuickReply(items = items)
    )
    app.line_bot_api.reply_message(
        event.reply_token,
        quick_reply_message
    )
    return
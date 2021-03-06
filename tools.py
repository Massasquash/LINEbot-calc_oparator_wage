from datetime import datetime as dt
import os, gspread
import api_settings


# Spreadsheet連携
credentials = api_settings.set_google_credentials()
gc = gspread.authorize(credentials)
ss_key = os.environ['SPREADSHEET_KEY']

ss = gc.open_by_key(ss_key)
record_sheet = ss.worksheet('record')
master_sheet = ss.worksheet('master')
cache_sheet = ss.worksheet('cache')

# マスター情報の取得
machines = master_sheet.get('B2:B6')
persons = master_sheet.get('B9:C18')

def get_user_sheet(event):
    user_id = event.source.user_id
    sheets_list = ss.worksheets()
    sheets_list = [sheets_list[i].title for i in range(len(sheets_list))]
    if user_id not in sheets_list:
        ss.duplicate_sheet(
            source_sheet_id = cache_sheet.id,
            new_sheet_name = user_id,
            insert_sheet_index = 3
    )
    return ss.worksheet(user_id)

def create_confirm_message(event):
    user_cache_sheet = get_user_sheet(event)
    cache = user_cache_sheet.get('B1:B5')

    starttime = dt.strptime(cache[0][0], '%Y-%m-%dT%H:%M')
    endtime = dt.strptime(cache[1][0], '%Y-%m-%dT%H:%M')
    seconds = (endtime - starttime).total_seconds()
    round_up_minutes = (seconds // 900 + 1) * 900 / 60
    starttime = starttime.strftime('%Y/%m/%d %H:%M')
    endtime = endtime.strftime('%Y/%m/%d %H:%M')
    totaltime = f'{int(round_up_minutes // 60):.0f}時間{int(round_up_minutes % 60):.0f}分'
    user_cache_sheet.update_acell('B5', round_up_minutes)

    msg = f'''この日報を登録しますか？
コンバイン：{cache[2][0]}
作業者：{cache[3][0]}\n
開始：{starttime}
終了：{endtime}
合計時間：{totaltime}\n
（※合計作業時間は15分単位・15分に満たない場合は切り上げで算出）'''

    return msg

def save_records(user_cache_sheet):
    cache = user_cache_sheet.get('B1:B5')
    record_sheet.append_row([cache[0][0], cache[1][0], cache[2][0], cache[3][0], cache[4][0]])




def calc_operator_wages():
    this_year = dt.now().year
    all_records = record_sheet.get_all_records()

    #レコードの内容を表示用に整形する
    records = [] #辞書型のリスト
    for record in all_records:
        record_year = dt.strptime(record['starttime'], '%Y-%m-%dT%H:%M').year
        record['date'] = record['starttime'][5:10].replace('-', '/')
        record['starttime'] = record['starttime'][-5:]
        del record['endtime']
        if record_year == this_year:
            records.append(record)

    records_per_day = {} #dateをキーとした辞書型のリスト
    for record in records:
        record_date = record['date']
        del record['date']
        if record_date in records_per_day:
            records_per_day[record_date].append(record)
        else:
            records_per_day[record_date] = [record]

    #①確認のテキストを作成
    msg_times_per_day = '今年度分のオペレーター作業履歴です。'
    for date in records_per_day.keys():
        msg_times_per_day += f'\n\n{date}'
        for record in records_per_day[date]:
            disp_worktime = f"{record['minutes'] // 60}h{record['minutes'] % 60}m"
            msg_times_per_day += f"\n・{record['machine'][:2]} {record['person'][:2]} {record['starttime']}〜（{disp_worktime}）"

    #②集計のテキストを作成
    total_time = {person[0]:0 for person in persons}
    for person in persons:
        for record in records:
            if record['person'] == person[0]:
                total_time[person[0]] += int(record['minutes'])

    msg_total_wages = '今年度分のオペレーター作業時間の合計と、賃金の集計結果です。\n'

    for person in total_time:
        wage = total_time[person] / 60 * 1300
        msg_total_wages += f'\n{person} : {total_time[person] // 60}h{total_time[person] % 60}m（{wage:,.0f}円）'

    return msg_times_per_day, msg_total_wages
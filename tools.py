from datetime import datetime as dt
import app
import gspread

def get_master_data():
    machines = app.master_sheet.get('B2:B6')
    persons = app.master_sheet.get('B9:B18')
    wages = app.master_sheet.get('B9:C18')

    return machines, persons, wages

def calc_operator_wages():
    this_year = dt.now().year
    all_records = app.record_sheet.get_all_records()

    #レコードの内容を表示用に整形する。
    #records:辞書型のリスト
    #ecords_per_day:dateをキーとした辞書型のリスト
    records = []
    for record in all_records:
        record_year = dt.strptime(record['starttime'], '%Y-%m-%dT%H:%M').year
        record['date'] = record['starttime'][5:9].replace('-', '/')
        record['starttime'] = record['starttime'][-5:]
        del record['endtime']
        if record_year == this_year:
            records.append(record)

    records_per_day = {}
    for record in records:
        record_date = record['date']
        del record['date']
        if record_date in records_per_day:
            records_per_day[record_date].append(record)
        else:
            records_per_day[record_date] = [record]
    

    #集計①のテキストを作成
    msg_times_per_day = '今年度分のオペレーター作業履歴です。'
    for date in records_per_day:
        msg_times_per_day += f'\n\n{date}'
        for record in records_per_day[date]:
            disp_worktime = f"{record['minutes'] // 60}h{record['minutes'] % 60}m"
            msg_times_per_day += f"\n・{record['machine']} {record['person']}\n\t\t{record['starttime']}開始（{disp_worktime}m稼働）"

    #集計②のテキストを作成
    total_time = {person[0]:0 for person in app.persons}
    for person in app.persons:
        for record in records:
            if record['person'] == person[0]:
                total_time[person[0]] += int(record['minutes'])

    msg_total_wages = '今年度分のオペレーター作業時間の合計と、賃金の集計結果です。\n'

    for person in total_time:
        wage = total_time[person] / 60 * 1300
        msg_total_wages += f'\n{person} : {total_time[person] // 60}h{total_time[person] % 60}m（{wage:.0f}円）'

    return msg_times_per_day, msg_total_wages
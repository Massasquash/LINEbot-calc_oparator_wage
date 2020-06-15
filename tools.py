import app

def get_master_data():
    machines = app.master_sheet.get('B2:B6')
    persons = app.master_sheet.get('B9:B18')

    return machines, persons
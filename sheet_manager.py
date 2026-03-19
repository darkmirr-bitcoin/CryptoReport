import gspread
from oauth2client.service_account import ServiceAccountCredentials

def update_google_sheet_bulk(data_rows):
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name("secrets.json", scope)
    client = gspread.authorize(creds)

    sheet_id = "1Sf0YRhmhE-x5oYIfUG7Io2gI8XclEvmOeQkqy-BY1pc"
    sheet = client.open_by_key(sheet_id)
    
    # --- 1. Today 탭 업데이트 ---
    worksheet_today = sheet.worksheet("Today")
    worksheet_today.batch_clear(["A2:Z1000"]) 
    worksheet_today.append_rows(data_rows, value_input_option='USER_ENTERED')
    
    # --- 2. History 탭 업데이트 ---
    worksheet_history = sheet.worksheet("History")
    worksheet_history.insert_rows(data_rows, row=2, value_input_option='USER_ENTERED')
    
    print(f"✅ 총 {len(data_rows)}개 코인 데이터 Today & History 시트 업데이트 완료!")
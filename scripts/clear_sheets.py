import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

def main():
    credentials_path = "credentials.json"
    spreadsheet_id = "1TlOwXH7BQyaLdI7MbiF0q2dbnWzoEKHNlQiqPlexw_4"

    if not os.path.exists(credentials_path):
        print("Credentials file not found!")
        return

    credentials = service_account.Credentials.from_service_account_file(
        credentials_path,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    service = build("sheets", "v4", credentials=credentials)

    # 1. Clear values from A8:T100
    range_to_clear = "'Лист1'!A8:T100"
    print(f"Clearing values in range: {range_to_clear}...")
    service.spreadsheets().values().clear(
        spreadsheetId=spreadsheet_id,
        range=range_to_clear
    ).execute()
    print("Values cleared successfully!")

    # 2. Reset formatting for rows 8 to 100
    print("Resetting formatting for rows 8 to 100...")
    requests = [
        {
            "repeatCell": {
                "range": {
                    "sheetId": 0,
                    "startRowIndex": 7,
                    "endRowIndex": 100,
                    "startColumnIndex": 0,
                    "endColumnIndex": 20
                },
                "cell": {
                    "userEnteredFormat": {}
                },
                "fields": "userEnteredFormat"
            }
        }
    ]
    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": requests}
    ).execute()
    print("Formatting reset successfully!")

if __name__ == "__main__":
    main()

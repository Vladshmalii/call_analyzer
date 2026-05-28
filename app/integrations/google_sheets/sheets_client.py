import asyncio
import os
from typing import Any
from google.oauth2 import service_account
from googleapiclient.discovery import build
import structlog
from app.core.config.settings import settings

logger = structlog.get_logger(__name__)

class GoogleSheetsClient:
    def __init__(self):
        self.credentials_path = settings.GOOGLE_CREDENTIALS_PATH
        self.spreadsheet_id = settings.GOOGLE_SHEET_ID
        self.service = None

    def _get_service(self):
        if not self.service:
            if not os.path.exists(self.credentials_path):
                logger.warning("Google credentials file not found, running sheets in mock/offline mode")
                return None
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=["https://www.googleapis.com/auth/spreadsheets"]
            )
            self.service = build("sheets", "v4", credentials=credentials)
        return self.service

    async def append_row(self, row_data: list[Any], needs_attention: bool = False) -> bool:
        return await asyncio.to_thread(self._append_row_sync, row_data, needs_attention)

    def _append_row_sync(self, row_data: list[Any], needs_attention: bool) -> bool:
        service = self._get_service()
        if not service:
            logger.warning("Google Sheets service could not be initialized (mock/offline mode)")
            return False

        try:
            logger.info("Fetching spreadsheet details", spreadsheet_id=self.spreadsheet_id)
            print(f"GOOGLE_SHEETS_CLIENT: Fetching details for spreadsheet_id={self.spreadsheet_id}...", flush=True)
            spreadsheet = service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
            sheets = spreadsheet.get("sheets", [])
            if not sheets:
                logger.error("No sheets found in the spreadsheet", spreadsheet_id=self.spreadsheet_id)
                print(f"GOOGLE_SHEETS_CLIENT ERROR: No sheets/tabs found in spreadsheet_id={self.spreadsheet_id}", flush=True)
                return False

            first_sheet_properties = sheets[0].get("properties", {})
            sheet_name = first_sheet_properties.get("title", "Sheet1")
            sheet_id = first_sheet_properties.get("sheetId", 0)

            logger.info("Resolved target sheet tab", sheet_name=sheet_name, sheet_id=sheet_id)
            print(f"GOOGLE_SHEETS_CLIENT: Resolved target sheet name='{sheet_name}', sheet_id={sheet_id}", flush=True)

            # Get all values in Column A to find the first truly empty row
            range_to_fetch = f"'{sheet_name}'!A:A"
            logger.info("Fetching Column A values to find the first empty row", range=range_to_fetch)
            print(f"GOOGLE_SHEETS_CLIENT: Fetching Column A values from range='{range_to_fetch}'...", flush=True)
            
            result_get = service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_to_fetch
            ).execute()
            values = result_get.get("values", [])

            first_empty_row = 2
            for i in range(1, len(values)):
                row_val = values[i]
                if not row_val or not str(row_val[0]).strip():
                    first_empty_row = i + 1
                    break
            else:
                first_empty_row = len(values) + 1

            if first_empty_row < 2:
                first_empty_row = 2

            body = {"values": [row_data]}
            target_range = f"'{sheet_name}'!A{first_empty_row}:T{first_empty_row}"
            logger.info("Updating row in Google Sheets", 
                        spreadsheet_id=self.spreadsheet_id, 
                        range=target_range, 
                        row_data=row_data)
            print(f"GOOGLE_SHEETS_CLIENT: Updating range='{target_range}'", flush=True)
            print(f"GOOGLE_SHEETS_CLIENT: Update values: {body}", flush=True)

            result = service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=target_range,
                valueInputOption="USER_ENTERED",
                body=body
            ).execute()

            logger.info("Google Sheets API update response", response=result)
            print(f"GOOGLE_SHEETS_CLIENT SUCCESS: Row updated successfully. Response: {result}", flush=True)

            row_index = first_empty_row
            logger.info("Successfully updated row index", row_index=row_index)
            print(f"GOOGLE_SHEETS_CLIENT: Resolved target row index={row_index}", flush=True)

            # Red highlighting disabled as per user request
            # if row_index and needs_attention:
            #     logger.info("Formatting row as red (needs attention)", row_index=row_index, sheet_id=sheet_id)
            #     print(f"GOOGLE_SHEETS_CLIENT: Formatting row {row_index} as red (needs attention)...", flush=True)
            #     self._format_row_red(service, row_index, sheet_id)


            return True
        except Exception as e:
            logger.error("Error appending row to Google Sheets", error=str(e), spreadsheet_id=self.spreadsheet_id, row_data=row_data)
            print(f"GOOGLE_SHEETS_CLIENT ERROR: Failed to append row. Spreadsheet={self.spreadsheet_id}, Error={str(e)}", flush=True)
            import traceback
            traceback.print_exc()
            return False

    def _parse_row_index(self, range_str: str) -> int | None:
        try:
            parts = range_str.split("!")[-1]
            row_part = "".join(c for c in parts.split(":")[0] if c.isdigit())
            return int(row_part)
        except Exception:
            return None

    def _format_row_red(self, service, row_index: int, sheet_id: int):
        try:
            logger.info("Sending batchUpdate formatting request to Google Sheets", row_index=row_index, sheet_id=sheet_id)
            requests = [
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": row_index - 1,
                            "endRowIndex": row_index,
                            "startColumnIndex": 0,
                            "endColumnIndex": 20
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": {
                                    "red": 1.0,
                                    "green": 0.85,
                                    "blue": 0.85
                                },
                                "textFormat": {
                                    "bold": True,
                                    "foregroundColor": {
                                        "red": 0.6,
                                        "green": 0.0,
                                        "blue": 0.0
                                    }
                                }
                            }
                        },
                        "fields": "userEnteredFormat(backgroundColor,textFormat)"
                    }
                }
            ]
            response = service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body={"requests": requests}
            ).execute()
            logger.info("Google Sheets formatting response", response=response)
        except Exception as e:
            logger.error("Failed to format cell background in Google Sheet", error=str(e))

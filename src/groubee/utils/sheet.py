from datetime import datetime

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from libs.utils.env import TRACKER_FILE_ID
from libs.utils.log import get_logger

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CREDENTIALS_FILE = "secrets/credentials.json"
TODAY = datetime.today().strftime("%d/%m/%Y")

log = get_logger(logs_to_file=True, logs_to_console=True)


def update_todays_balance(account: str, balance: float, amount: float, machine: str):
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    service = build("sheets", "v4", credentials=creds)

    sheet = service.spreadsheets()
    cell_range = f"{account}!A1:F"
    result = (
        sheet.values().get(spreadsheetId=TRACKER_FILE_ID, range=cell_range).execute()
    )
    values = result.get("values", [])

    if not values:
        log.warning("Update was not performed as no values found in the worksheet")
        return

    for row_idx, row in enumerate(values):
        for col_idx, col in enumerate(row):
            if col.strip() == TODAY:
                # Skip todays update, if exists
                populated_cells = [cell for cell in row if cell]
                if len(populated_cells) != 1:
                    log.info("Skipping - Today's balance has already been updated!")
                    return

                # Adjust for sheets 1-based indexing
                row_number = row_idx + 1

                # Columns B = Value, D = Amount, E = Machine
                updates = {
                    f"{account}!B{row_number}": balance,
                    f"{account}!D{row_number}": amount,
                    f"{account}!E{row_number}": machine,
                }

                # Perform updates
                for cell_range, value in updates.items():
                    sheet.values().update(
                        spreadsheetId=TRACKER_FILE_ID,
                        range=cell_range,
                        valueInputOption="RAW",
                        body={"values": [[value]]},
                    ).execute()
                    log.info(f"Successfully updated {cell_range} with '{value}'!")
                return

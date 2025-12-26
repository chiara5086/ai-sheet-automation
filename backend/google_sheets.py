import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_INFO = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')

if SERVICE_ACCOUNT_INFO:
    SERVICE_ACCOUNT_INFO = json.loads(SERVICE_ACCOUNT_INFO)


def get_service():
    creds = service_account.Credentials.from_service_account_info(
        SERVICE_ACCOUNT_INFO, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    return service


def get_sheet_data(spreadsheet_id, range_name):
    service = get_service()
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
    return result.get('values', [])


def update_sheet_data(spreadsheet_id, range_name, values):
    service = get_service()
    sheet = service.spreadsheets()
    body = {'values': values}
    result = sheet.values().update(
        spreadsheetId=spreadsheet_id, range=range_name,
        valueInputOption='USER_ENTERED', body=body).execute()
    return result


def format_cell_color(spreadsheet_id, sheet_name, column_letter, row_num, color_hex):
    """
    Apply background color to a specific cell in Google Sheets.
    
    Args:
        spreadsheet_id: The ID of the spreadsheet
        sheet_name: The name of the sheet/tab (can be None for default)
        column_letter: The column letter (e.g., 'A', 'B', 'AC')
        row_num: The row number (1-indexed)
        color_hex: Hex color code (e.g., '#fff2cc' for light yellow)
    
    Returns:
        The result of the batchUpdate operation
    """
    service = get_service()
    sheet = service.spreadsheets()
    
    # Convert hex color to RGB (Google Sheets API uses RGB values 0-1)
    # Remove '#' if present
    color_hex = color_hex.lstrip('#')
    # Convert to RGB
    r = int(color_hex[0:2], 16) / 255.0
    g = int(color_hex[2:4], 16) / 255.0
    b = int(color_hex[4:6], 16) / 255.0
    
    # Build the range
    if sheet_name:
        range_name = f"{sheet_name}!{column_letter}{row_num}"
    else:
        range_name = f"{column_letter}{row_num}"
    
    # Get sheet ID (we need the sheet ID, not the name)
    spreadsheet = sheet.get(spreadsheetId=spreadsheet_id).execute()
    sheet_id = None
    for s in spreadsheet.get('sheets', []):
        if sheet_name is None or s['properties']['title'] == sheet_name:
            sheet_id = s['properties']['sheetId']
            break
    
    if sheet_id is None:
        print(f"WARNING: Could not find sheet '{sheet_name}' for coloring. Skipping color formatting.")
        return None
    
    # Build the request to format the cell
    requests = [{
        'repeatCell': {
            'range': {
                'sheetId': sheet_id,
                'startRowIndex': row_num - 1,  # Convert to 0-indexed
                'endRowIndex': row_num,
                'startColumnIndex': _column_letter_to_index(column_letter),
                'endColumnIndex': _column_letter_to_index(column_letter) + 1
            },
            'cell': {
                'userEnteredFormat': {
                    'backgroundColor': {
                        'red': r,
                        'green': g,
                        'blue': b
                    }
                }
            },
            'fields': 'userEnteredFormat.backgroundColor'
        }
    }]
    
    body = {'requests': requests}
    result = sheet.batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
    return result


def _column_letter_to_index(column_letter):
    """
    Convert column letter (e.g., 'A', 'B', 'AC') to 0-based index.
    """
    result = 0
    for char in column_letter:
        result = result * 26 + (ord(char.upper()) - ord('A') + 1)
    return result - 1
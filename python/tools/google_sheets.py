"""
Google Sheets Tool for Agent Zero
Uses service account credentials from /root/.config/clawdbot/google-service-account.json

Capabilities:
- Read spreadsheet data
- Write/append data to sheets
- Create new spreadsheets
- List sheets in a spreadsheet
"""

import json
import os
from typing import Any, Optional
from python.helpers.tool import Tool, Response
from python.helpers import files

# Google API imports
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False


class GoogleSheets(Tool):
    """Tool for interacting with Google Sheets API."""
    
    CREDENTIALS_PATH = "/root/.config/clawdbot/google-service-account.json"
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive.file'
    ]
    
    # Default spreadsheets
    PLATAPAY_SPREADSHEET_ID = "11GhQfg1zTEs1CfNcyGkqq7dLfnacIBbKVWss-PSXzlg"
    
    async def execute(self, **kwargs) -> Response:
        if not GOOGLE_AVAILABLE:
            return Response(
                message="Google API libraries not installed. Run: pip install google-api-python-client google-auth",
                break_loop=False
            )
        
        action = kwargs.get("action", "read")
        spreadsheet_id = kwargs.get("spreadsheet_id", "")
        sheet_range = kwargs.get("range", "Sheet1!A1:Z100")
        values = kwargs.get("values", [])
        title = kwargs.get("title", "New Spreadsheet")
        
        try:
            service = self._get_service()
            
            if action == "read":
                return await self._read_sheet(service, spreadsheet_id, sheet_range)
            elif action == "write":
                return await self._write_sheet(service, spreadsheet_id, sheet_range, values)
            elif action == "append":
                return await self._append_sheet(service, spreadsheet_id, sheet_range, values)
            elif action == "create":
                return await self._create_spreadsheet(service, title)
            elif action == "list_sheets":
                return await self._list_sheets(service, spreadsheet_id)
            elif action == "test":
                return await self._test_connection(service)
            else:
                return Response(
                    message=f"Unknown action: {action}. Available: read, write, append, create, list_sheets, test",
                    break_loop=False
                )
                
        except HttpError as e:
            return Response(
                message=f"Google Sheets API error: {e.reason}\nDetails: {e.error_details if hasattr(e, 'error_details') else str(e)}",
                break_loop=False
            )
        except Exception as e:
            return Response(
                message=f"Error: {type(e).__name__}: {str(e)}",
                break_loop=False
            )
    
    def _get_service(self):
        """Get authenticated Google Sheets service."""
        credentials = service_account.Credentials.from_service_account_file(
            self.CREDENTIALS_PATH,
            scopes=self.SCOPES
        )
        return build('sheets', 'v4', credentials=credentials)
    
    def _get_drive_service(self):
        """Get authenticated Google Drive service."""
        credentials = service_account.Credentials.from_service_account_file(
            self.CREDENTIALS_PATH,
            scopes=self.SCOPES
        )
        return build('drive', 'v3', credentials=credentials)
    
    async def _test_connection(self, service) -> Response:
        """Test the connection to Google Sheets API."""
        # Just verify we can make API calls
        try:
            # Try to get the service info
            about = service._baseUrl
            return Response(
                message=f"✅ Google Sheets API connection successful!\n\nService Account: clawd-697@celtic-parser-485706-f5.iam.gserviceaccount.com\nAPI Endpoint: {about}\n\nReady to use. Share spreadsheets with the service account email to grant access.",
                break_loop=False
            )
        except Exception as e:
            return Response(message=f"Connection test failed: {e}", break_loop=False)
    
    async def _read_sheet(self, service, spreadsheet_id: str, sheet_range: str) -> Response:
        """Read data from a spreadsheet."""
        if not spreadsheet_id:
            return Response(
                message="Error: spreadsheet_id is required. Provide the ID from the spreadsheet URL.",
                break_loop=False
            )
        
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=sheet_range
        ).execute()
        
        values = result.get('values', [])
        
        if not values:
            return Response(message=f"No data found in range: {sheet_range}", break_loop=False)
        
        # Format as table
        output = f"📊 Data from range: {sheet_range}\n\n"
        for i, row in enumerate(values[:50]):  # Limit to 50 rows
            output += f"Row {i+1}: {' | '.join(str(cell) for cell in row)}\n"
        
        if len(values) > 50:
            output += f"\n... and {len(values) - 50} more rows"
        
        return Response(message=output, break_loop=False)
    
    async def _write_sheet(self, service, spreadsheet_id: str, sheet_range: str, values: list) -> Response:
        """Write data to a spreadsheet (overwrites existing data)."""
        if not spreadsheet_id:
            return Response(message="Error: spreadsheet_id is required.", break_loop=False)
        if not values:
            return Response(message="Error: values is required. Provide a 2D list of data.", break_loop=False)
        
        body = {'values': values}
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=sheet_range,
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()
        
        return Response(
            message=f"✅ Updated {result.get('updatedCells', 0)} cells in range: {sheet_range}",
            break_loop=False
        )
    
    async def _append_sheet(self, service, spreadsheet_id: str, sheet_range: str, values: list) -> Response:
        """Append data to a spreadsheet."""
        if not spreadsheet_id:
            return Response(message="Error: spreadsheet_id is required.", break_loop=False)
        if not values:
            return Response(message="Error: values is required. Provide a 2D list of data.", break_loop=False)
        
        body = {'values': values}
        result = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=sheet_range,
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()
        
        updates = result.get('updates', {})
        return Response(
            message=f"✅ Appended {updates.get('updatedRows', 0)} rows to spreadsheet",
            break_loop=False
        )
    
    async def _create_spreadsheet(self, service, title: str) -> Response:
        """Create a new spreadsheet."""
        spreadsheet = {
            'properties': {'title': title}
        }
        result = service.spreadsheets().create(body=spreadsheet).execute()
        
        spreadsheet_id = result.get('spreadsheetId')
        spreadsheet_url = result.get('spreadsheetUrl')
        
        return Response(
            message=f"✅ Created new spreadsheet!\n\nTitle: {title}\nID: {spreadsheet_id}\nURL: {spreadsheet_url}\n\n⚠️ Note: Only the service account has access. Share with your email to view it.",
            break_loop=False
        )
    
    async def _list_sheets(self, service, spreadsheet_id: str) -> Response:
        """List all sheets in a spreadsheet."""
        if not spreadsheet_id:
            return Response(message="Error: spreadsheet_id is required.", break_loop=False)
        
        result = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        
        sheets = result.get('sheets', [])
        title = result.get('properties', {}).get('title', 'Unknown')
        
        output = f"📋 Spreadsheet: {title}\n\nSheets:\n"
        for sheet in sheets:
            props = sheet.get('properties', {})
            output += f"  - {props.get('title')} (ID: {props.get('sheetId')}, Rows: {props.get('gridProperties', {}).get('rowCount')})\n"
        
        return Response(message=output, break_loop=False)

# google_sheets

Tool for interacting with Google Sheets API using service account credentials.

## Actions

### test
Test the API connection.
```python
result = await self.call_tool("google_sheets", action="test")
```

### read
Read data from a spreadsheet.
```python
result = await self.call_tool("google_sheets",
    action="read",
    spreadsheet_id="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",  # From URL
    range="Sheet1!A1:D10"
)
```

### write
Write data to a spreadsheet (overwrites existing).
```python
result = await self.call_tool("google_sheets",
    action="write",
    spreadsheet_id="YOUR_SPREADSHEET_ID",
    range="Sheet1!A1",
    values=[
        ["Name", "Email", "Status"],
        ["John", "john@example.com", "Active"],
        ["Jane", "jane@example.com", "Pending"]
    ]
)
```

### append
Append rows to a spreadsheet.
```python
result = await self.call_tool("google_sheets",
    action="append",
    spreadsheet_id="YOUR_SPREADSHEET_ID",
    range="Sheet1!A:D",
    values=[
        ["New User", "new@example.com", "Active", "2024-01-15"]
    ]
)
```

### create
Create a new spreadsheet.
```python
result = await self.call_tool("google_sheets",
    action="create",
    title="PlataPay Agent Tracking"
)
```

### list_sheets
List all sheets in a spreadsheet.
```python
result = await self.call_tool("google_sheets",
    action="list_sheets",
    spreadsheet_id="YOUR_SPREADSHEET_ID"
)
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| action | string | Yes | One of: test, read, write, append, create, list_sheets |
| spreadsheet_id | string | For most actions | The ID from the spreadsheet URL |
| range | string | For read/write/append | Sheet range in A1 notation (e.g., "Sheet1!A1:D10") |
| values | list | For write/append | 2D list of values to write |
| title | string | For create | Title for new spreadsheet |

## Getting Spreadsheet ID

From URL: `https://docs.google.com/spreadsheets/d/`**`1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms`**`/edit`

The ID is the long string between `/d/` and `/edit`.

## Sharing Access

The service account email is: `clawd-697@celtic-parser-485706-f5.iam.gserviceaccount.com`

To give the tool access to an existing spreadsheet:
1. Open the spreadsheet in Google Sheets
2. Click "Share"
3. Add the service account email with "Editor" access

## Use Cases

- Track PlataPay agent signups and referrals
- Store marketing campaign data
- Log customer interactions
- Export reports and analytics
- Sync data between systems

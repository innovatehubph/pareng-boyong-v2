---
name: google-sheets
description: Read and write Google Sheets data. Manage spreadsheets, update cells, and query data.
version: 1.0.0
author: InnovateHub
tags:
  - google
  - sheets
  - spreadsheet
  - data
triggers:
  - google sheets
  - spreadsheet
  - update sheet
  - read sheet
allowed_tools:
  - code_execution_tool
---

# Google Sheets Integration

Read and write Google Sheets programmatically.

## Setup
Requires Google service account credentials at:
`/a0/google-service-account.json`

## Usage

### Read Data
```python
response = google_sheets(
    action="read",
    spreadsheet_id="your-spreadsheet-id",
    range="Sheet1!A1:D10"
)
```

### Write Data
```python
response = google_sheets(
    action="write",
    spreadsheet_id="your-spreadsheet-id",
    range="Sheet1!A1",
    values=[["Name", "Email"], ["John", "john@example.com"]]
)
```

### Append Row
```python
response = google_sheets(
    action="append",
    spreadsheet_id="your-spreadsheet-id",
    range="Sheet1",
    values=[["New", "Row", "Data"]]
)
```

# Google Sheets Configuration

## PlataPay Agent Tracking Spreadsheet

**Spreadsheet ID:** `11GhQfg1zTEs1CfNcyGkqq7dLfnacIBbKVWss-PSXzlg`
**URL:** https://docs.google.com/spreadsheets/d/11GhQfg1zTEs1CfNcyGkqq7dLfnacIBbKVWss-PSXzlg

### Sheets

#### 1. Agents
Track PlataPay agent signups and performance.

| Column | Description |
|--------|-------------|
| Agent ID | Unique identifier |
| Name | Agent's full name |
| Email | Contact email |
| Phone | Contact phone |
| Status | Active/Pending/Inactive |
| Signup Date | When they joined |
| Referrer ID | Who referred them |
| Total Referrals | Number of agents they've referred |
| Commission Earned | Total commission in PHP |

#### 2. Referrals
Track referral relationships between agents.

| Column | Description |
|--------|-------------|
| Referral ID | Unique referral identifier |
| Referrer Agent ID | Agent who made the referral |
| Referred Agent ID | New agent who was referred |
| Date | Referral date |
| Status | Pending/Approved/Rejected |
| Commission | Commission amount in PHP |

#### 3. Analytics
Daily metrics and KPIs.

| Column | Description |
|--------|-------------|
| Date | Report date |
| New Signups | New agents that day |
| Active Agents | Currently active agents |
| Total Transactions | Transaction count |
| Total Revenue | Revenue in PHP |
| Commission Paid | Commissions paid out |

## Quick Usage

```python
# Read agents
result = await self.call_tool("google_sheets",
    action="read",
    spreadsheet_id="11GhQfg1zTEs1CfNcyGkqq7dLfnacIBbKVWss-PSXzlg",
    range="Agents!A:I"
)

# Add new agent
result = await self.call_tool("google_sheets",
    action="append",
    spreadsheet_id="11GhQfg1zTEs1CfNcyGkqq7dLfnacIBbKVWss-PSXzlg",
    range="Agents!A:I",
    values=[["AGT001", "Juan Dela Cruz", "juan@email.com", "+639123456789", "Active", "2024-02-02", "", "0", "0"]]
)

# Log daily analytics
result = await self.call_tool("google_sheets",
    action="append",
    spreadsheet_id="11GhQfg1zTEs1CfNcyGkqq7dLfnacIBbKVWss-PSXzlg",
    range="Analytics!A:F",
    values=[["2024-02-02", "5", "120", "350", "45000", "2500"]]
)
```

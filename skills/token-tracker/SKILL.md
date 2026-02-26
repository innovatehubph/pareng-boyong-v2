# Token Usage Tracker & Analyzer

**Version:** 1.0.0
**Author:** Pareng Boyong (Agent Zero)
**Tags:** tokens, monitoring, analytics, claude, billing, usage-tracking

## Description

Comprehensive token usage tracking, monitoring, and analysis skill for all AI agents
and bots running under Boss Marc's Claude Max subscription. Parses multiple data sources
(HTML logs, chat.json files, JSONL tracking, bot directories) to produce accurate
token consumption reports.

## Capabilities

- **Parse HTML Logs** - Extract exact cache creation/read tokens from Agent Zero logs
- **Parse Chat Sessions** - Analyze chat.json files for message token counts
- **Estimate Total Usage** - Calculate total tokens including system prompt and history overhead
- **Monitor Bots** - Check ClawdBot and OpenClaw for token usage data
- **Daily Summaries** - Quick view of today's consumption
- **Export Data** - JSON and CSV export for external analysis
- **API Hook** - Optional hook for exact per-call token tracking

## Data Sources & Reliability

| Source | Reliability | What It Captures |
|--------|-------------|------------------|
| HTML Logs (cache stats) | **Exact** | Cache creation & read tokens from Anthropic API |
| chat.json (msg tokens) | **Exact** | Per-message token counts from framework tokenizer |
| API Hook (JSONL) | **Exact** | Full input/output/cache per API call (requires install) |
| Estimated Total | **Estimate** | Includes system prompt + tool defs + history overhead |

## Quick Start

### Generate Full Report
```bash
python3 /a0/skills/token-tracker/scripts/token_tracker.py report
```

### Today's Summary
```bash
python3 /a0/skills/token-tracker/scripts/token_tracker.py daily
```

### List All Chats
```bash
python3 /a0/skills/token-tracker/scripts/token_tracker.py chats
```

### Analyze Specific Chat
```bash
python3 /a0/skills/token-tracker/scripts/token_tracker.py analyze <chat_id>
```

### Check Bot Usage
```bash
python3 /a0/skills/token-tracker/scripts/token_tracker.py bots
```

### Check API Hook Status
```bash
python3 /a0/skills/token-tracker/scripts/token_tracker.py hook-status
```

### Export Data
```bash
python3 /a0/skills/token-tracker/scripts/token_tracker.py export json
python3 /a0/skills/token-tracker/scripts/token_tracker.py export csv
```

### Parse Logs by Date
```bash
python3 /a0/skills/token-tracker/scripts/token_tracker.py logs 20260218
```

## Install API Hook (Optional - For Exact Tracking)

The API hook intercepts every LLM call and logs exact token counts:

```bash
python3 /a0/skills/token-tracker/scripts/install_hook.py          # Install
python3 /a0/skills/token-tracker/scripts/install_hook.py --check   # Check status
python3 /a0/skills/token-tracker/scripts/install_hook.py --remove  # Remove
```

## Estimation Formula

Without the API hook, total tokens are estimated per chat:

```
N = number of AI responses in chat
overhead_per_call = 12,000 (system prompt) + 8,000 (tool definitions)
avg_history = total_message_tokens * (N+1) / (2*N)
estimated_total = N * (overhead + avg_history) + output_tokens
```

This accounts for the growing conversation history that gets sent with each API call.

## Agents Tracked

| Agent | Platform | Tracking Method |
|-------|----------|----------------|
| Pareng Boyong | Docker (Agent Zero) | HTML logs + chat.json + optional hook |
| ClawdBot | systemd (Claude Code) | .claude directory inspection |
| OpenClaw | PM2 (Claude Code) | PM2 logs inspection |

## File Structure

```
/a0/skills/token-tracker/
├── SKILL.md                          # This file
└── scripts/
    ├── token_tracker.py              # Main tracker (744 lines)
    └── install_hook.py               # API hook installer (198 lines)

/a0/tmp/token_tracking/               # Runtime data
├── usage_log.jsonl                   # API hook records (if installed)
└── hook_status.json                  # Hook installation status
```

## Output Formats

- **Markdown Report** - Full formatted report with tables
- **JSON Export** - Machine-readable with all data
- **CSV Export** - Spreadsheet-compatible chat summary

## Notes

- Claude Max subscription has no per-token billing, but tracking helps monitor usage patterns
- Telegram bots (ClawdBot, OpenClaw) use Claude Code which has its own token tracking
- The estimation formula tends to slightly overestimate due to prompt caching reducing actual tokens sent
- For exact data, install the API hook or check provider dashboards directly

#!/usr/bin/env python3
"""
Token Usage Tracker & Analyzer for Claude Max Subscription
==========================================================
Tracks, monitors, and analyzes token consumption across all AI agents/bots
using the Claude Max subscription on Boss Marc's VPS.

Supported agents:
- Pareng Boyong (Agent Zero) - Docker container
- ClawdBot (@bossmarc_serverbot) - systemd service  
- OpenClaw (@bossabossbot) - PM2 service

Data sources:
- Agent Zero HTML logs (cache stats per API call)
- Agent Zero chat.json (per-message token counts)
- Anthropic API usage data (via hook)
- Token usage JSONL tracking file
- Telegram bot logs

Usage:
    python3 token_tracker.py report              # Full report
    python3 token_tracker.py analyze <chat_id>    # Analyze specific chat
    python3 token_tracker.py daily                # Today's summary
    python3 token_tracker.py compare <id1> <id2>  # Compare chats
    python3 token_tracker.py logs [date]           # Parse logs
    python3 token_tracker.py chats                # List all chats with tokens
    python3 token_tracker.py bots                 # Check all bot usage
    python3 token_tracker.py export [json|csv]    # Export data
    python3 token_tracker.py hook-status          # Check if API hook is active
"""

import os
import re
import json
import sys
import glob
import time
import csv
import io
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from collections import defaultdict

# ============================================================
# CONFIGURATION
# ============================================================

A0_BASE = "/a0"
A0_LOGS_DIR = os.path.join(A0_BASE, "logs")
A0_CHATS_DIR = os.path.join(A0_BASE, "tmp", "chats")
A0_TRACKING_DIR = os.path.join(A0_BASE, "tmp", "token_tracking")
A0_TRACKING_FILE = os.path.join(A0_TRACKING_DIR, "usage_log.jsonl")
A0_HOOK_STATUS_FILE = os.path.join(A0_TRACKING_DIR, "hook_status.json")

VPS_BASE = "/vps"
CLAWDBOT_DIR = os.path.join(VPS_BASE, "root", "clawd")
OPENCLAW_DIR = os.path.join(VPS_BASE, "srv", "apps", "bossm-assistant")

# Token estimation constants
SYSTEM_PROMPT_TOKENS = 12000   # Typical A0 system prompt
TOOL_DEFS_TOKENS = 8000       # Tool definitions overhead
AVG_CHARS_PER_TOKEN = 4.0

os.makedirs(A0_TRACKING_DIR, exist_ok=True)

# ============================================================
# DATA CLASSES
# ============================================================

@dataclass
class TokenRecord:
    timestamp: str
    agent: str
    model: str = ""
    chat_id: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_tokens: int = 0
    cache_read_tokens: int = 0
    total_tokens: int = 0
    source: str = ""
    
    def __post_init__(self):
        if self.total_tokens == 0:
            self.total_tokens = (self.input_tokens + self.output_tokens +
                                self.cache_creation_tokens + self.cache_read_tokens)

@dataclass
class ChatAnalysis:
    chat_id: str
    chat_name: str
    created_at: str
    agent: str = "pareng-boyong"
    message_count: int = 0
    ai_messages: int = 0
    user_messages: int = 0
    total_message_tokens: int = 0
    estimated_input: int = 0
    estimated_output: int = 0
    cache_creation: int = 0
    cache_read: int = 0
    estimated_total: int = 0
    tool_calls: int = 0
    subordinate_calls: int = 0
    api_calls_in_log: int = 0
    log_file: str = ""

# ============================================================
# LOG PARSER
# ============================================================

CACHE_PATTERN = re.compile(r"Cache: created=(\d+), read=(\d+) tokens")
LOG_TS_PATTERN = re.compile(r"log_(\d{8})_(\d{6})\.html")

def parse_log_file(filepath):
    """Parse single HTML log for cache stats."""
    result = {
        "file": os.path.basename(filepath),
        "timestamp": None,
        "cache_entries": [],
        "total_cache_creation": 0,
        "total_cache_read": 0,
        "api_calls": 0,
        "file_size": os.path.getsize(filepath),
    }
    m = LOG_TS_PATTERN.search(os.path.basename(filepath))
    if m:
        d, t = m.group(1), m.group(2)
        result["timestamp"] = f"{d[:4]}-{d[4:6]}-{d[6:8]}T{t[:2]}:{t[2:4]}:{t[4:6]}"
    
    try:
        with open(filepath, "r", errors="ignore") as f:
            content = f.read()
        for created, read in CACHE_PATTERN.findall(content):
            c, r = int(created), int(read)
            result["cache_entries"].append({"creation": c, "read": r})
            result["total_cache_creation"] += c
            result["total_cache_read"] += r
            result["api_calls"] += 1
    except Exception as e:
        result["error"] = str(e)
    return result

def parse_all_logs(date_filter=None):
    """Parse all log files, optionally filtered by date (YYYYMMDD)."""
    results = []
    if not os.path.exists(A0_LOGS_DIR):
        return results
    for fn in sorted(os.listdir(A0_LOGS_DIR)):
        if not fn.endswith(".html"):
            continue
        if date_filter and date_filter not in fn:
            continue
        fp = os.path.join(A0_LOGS_DIR, fn)
        r = parse_log_file(fp)
        if r["api_calls"] > 0 or r["file_size"] > 500:
            results.append(r)
    return results

def find_log_for_date(date_str):
    """Find the largest log file for a given date."""
    compact = date_str.replace("-", "")
    logs = []
    for fn in os.listdir(A0_LOGS_DIR):
        if compact in fn and fn.endswith(".html"):
            fp = os.path.join(A0_LOGS_DIR, fn)
            logs.append((fp, os.path.getsize(fp)))
    if logs:
        return max(logs, key=lambda x: x[1])[0]
    return None

# ============================================================
# CHAT PARSER
# ============================================================

def parse_chat(chat_id):
    """Parse a single chat.json for token analysis."""
    cj = os.path.join(A0_CHATS_DIR, chat_id, "chat.json")
    if not os.path.exists(cj):
        return None
    try:
        with open(cj) as f:
            data = json.load(f)
    except Exception:
        return None
    
    a = ChatAnalysis(
        chat_id=chat_id,
        chat_name=data.get("name", "Unknown"),
        created_at=data.get("created_at", ""),
    )
    
    for agent in data.get("agents", []):
        if not isinstance(agent, dict):
            continue
        history = agent.get("history", "")
        if isinstance(history, str):
            try:
                history = json.loads(history)
            except (json.JSONDecodeError, TypeError):
                continue
        if not isinstance(history, dict):
            continue
        
        topics = history.get("topics", [])
        current = history.get("current", {})
        all_topics = topics + ([current] if current and isinstance(current, dict) else [])
        
        for topic in all_topics:
            if not isinstance(topic, dict):
                continue
            for msg in topic.get("messages", []):
                if not isinstance(msg, dict):
                    continue
                tokens = msg.get("tokens", 0)
                is_ai = msg.get("ai", False)
                content = msg.get("content", "")
                
                a.message_count += 1
                a.total_message_tokens += tokens
                
                if is_ai:
                    a.ai_messages += 1
                    a.estimated_output += tokens
                    if isinstance(content, str):
                        if '"tool_name"' in content:
                            a.tool_calls += 1
                        if 'call_subordinate' in content:
                            a.subordinate_calls += 1
                else:
                    a.user_messages += 1
                    a.estimated_input += tokens
    
    # Estimate total tokens including overhead
    # Each AI response = 1 API call with system prompt + history + tools
    n_calls = a.ai_messages
    if n_calls > 0:
        # Progressive history accumulation model:
        # Call 1: sys + tools + msg1
        # Call N: sys + tools + msg1..msgN
        # Average history per call ≈ total_message_tokens * (N+1) / (2*N)
        avg_history = a.total_message_tokens * (n_calls + 1) / (2 * n_calls) if n_calls > 0 else 0
        overhead_per_call = SYSTEM_PROMPT_TOKENS + TOOL_DEFS_TOKENS
        a.estimated_total = int(n_calls * (overhead_per_call + avg_history) + a.estimated_output)
    
    # Try to find associated log file
    if a.created_at:
        try:
            dt = datetime.fromisoformat(a.created_at.replace("Z", "+00:00"))
            date_compact = dt.strftime("%Y%m%d")
            log_fp = find_log_for_date(dt.strftime("%Y-%m-%d"))
            if log_fp:
                a.log_file = os.path.basename(log_fp)
                ld = parse_log_file(log_fp)
                a.cache_creation = ld["total_cache_creation"]
                a.cache_read = ld["total_cache_read"]
                a.api_calls_in_log = ld["api_calls"]
        except Exception:
            pass
    
    return a

def parse_all_chats():
    """Parse all chat sessions."""
    results = []
    if not os.path.exists(A0_CHATS_DIR):
        return results
    for cid in sorted(os.listdir(A0_CHATS_DIR)):
        if not os.path.isdir(os.path.join(A0_CHATS_DIR, cid)):
            continue
        a = parse_chat(cid)
        if a and a.message_count > 0:
            results.append(a)
    return results

# ============================================================
# TELEGRAM BOT PARSERS
# ============================================================

def parse_clawdbot():
    """Check ClawdBot for token usage data."""
    result = {"agent": "clawdbot", "bot": "@bossmarc_serverbot", "status": "unknown",
              "files": [], "usage": {}, "notes": []}
    if not os.path.exists(CLAWDBOT_DIR):
        result["status"] = "not_found"
        return result
    result["status"] = "found"
    
    # Check .claude dir
    claude_dir = os.path.join(CLAWDBOT_DIR, ".claude")
    if os.path.exists(claude_dir):
        result["notes"].append("Uses Claude Code (.claude dir found)")
        for f in os.listdir(claude_dir):
            fp = os.path.join(claude_dir, f)
            result["files"].append(fp)
            if f.endswith(".json"):
                try:
                    with open(fp) as fh:
                        d = json.load(fh)
                    if isinstance(d, dict):
                        result["usage"][f] = {k: v for k, v in d.items() 
                                             if any(kw in k.lower() for kw in ["token", "usage", "cost", "model"])}
                except Exception:
                    pass
    
    # Check memory dir
    mem_dir = os.path.join(CLAWDBOT_DIR, "memory")
    if os.path.exists(mem_dir):
        mem_files = []
        for root, dirs, files in os.walk(mem_dir):
            mem_files.extend([os.path.join(root, f) for f in files])
        result["notes"].append(f"Memory dir: {len(mem_files)} files")
    
    return result

def parse_openclaw():
    """Check OpenClaw for token usage data."""
    result = {"agent": "openclaw", "bot": "@bossabossbot", "status": "unknown",
              "files": [], "usage": {}, "notes": []}
    if not os.path.exists(OPENCLAW_DIR):
        result["status"] = "not_found"
        return result
    result["status"] = "found"
    
    # Check PM2 logs
    for logname in ["bossm-assistant-out.log", "bossm-assistant-error.log"]:
        lp = f"/vps/root/.pm2/logs/{logname}"
        if os.path.exists(lp):
            result["files"].append(lp)
            try:
                with open(lp) as f:
                    lines = f.readlines()[-200:]
                token_lines = [l.strip() for l in lines if "token" in l.lower() or "usage" in l.lower()]
                if token_lines:
                    result["usage"][logname] = token_lines[:10]
            except Exception:
                pass
    
    return result

# ============================================================
# TRACKING FILE (JSONL)
# ============================================================

def append_tracking_record(record: TokenRecord):
    """Append record to JSONL tracking file."""
    with open(A0_TRACKING_FILE, "a") as f:
        f.write(json.dumps(asdict(record)) + "\n")

def read_tracking_records(date_filter=None, agent_filter=None):
    """Read records from JSONL file."""
    records = []
    if not os.path.exists(A0_TRACKING_FILE):
        return records
    with open(A0_TRACKING_FILE) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                r = TokenRecord(**d)
                if date_filter and not r.timestamp.startswith(date_filter):
                    continue
                if agent_filter and r.agent != agent_filter:
                    continue
                records.append(r)
            except Exception:
                continue
    return records

# ============================================================
# HOOK STATUS
# ============================================================

def check_hook_status():
    """Check if the API hook is active in innovatehub_claude.py."""
    hook_file = "/a0/python/helpers/innovatehub_claude.py"
    status = {"hooked": False, "tracking_file_exists": os.path.exists(A0_TRACKING_FILE),
              "tracking_records": 0, "last_record": None}
    
    if os.path.exists(hook_file):
        with open(hook_file) as f:
            content = f.read()
        status["hooked"] = "token_tracker_hook" in content or "append_tracking_record" in content
    
    if os.path.exists(A0_TRACKING_FILE):
        with open(A0_TRACKING_FILE) as f:
            lines = [l for l in f if l.strip()]
        status["tracking_records"] = len(lines)
        if lines:
            try:
                status["last_record"] = json.loads(lines[-1])
            except Exception:
                pass
    
    return status

# ============================================================
# REPORT GENERATORS
# ============================================================

def fmt_tokens(n):
    """Format token count with commas."""
    if n >= 1_000_000:
        return f"{n:,.0f} ({n/1_000_000:.2f}M)"
    elif n >= 1_000:
        return f"{n:,.0f} ({n/1_000:.1f}K)"
    return f"{n:,}"

def generate_report():
    """Generate full markdown report."""
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")
    today_c = now.strftime("%Y%m%d")
    
    # Parse all data sources
    all_logs = parse_all_logs()
    today_logs = parse_all_logs(date_filter=today_c)
    all_chats = parse_all_chats()
    clawdbot = parse_clawdbot()
    openclaw = parse_openclaw()
    hook = check_hook_status()
    
    # Aggregate
    total_cache_creation = sum(l["total_cache_creation"] for l in all_logs)
    total_cache_read = sum(l["total_cache_read"] for l in all_logs)
    total_api_calls = sum(l["api_calls"] for l in all_logs)
    total_msg_tokens = sum(c.total_message_tokens for c in all_chats)
    total_estimated = sum(c.estimated_total for c in all_chats)
    
    today_cc = sum(l["total_cache_creation"] for l in today_logs)
    today_cr = sum(l["total_cache_read"] for l in today_logs)
    today_calls = sum(l["api_calls"] for l in today_logs)
    
    cache_total = total_cache_creation + total_cache_read
    cache_hit = (total_cache_read / cache_total * 100) if cache_total > 0 else 0
    
    # Build report
    lines = []
    lines.append(f"# 📊 Token Usage Report - Claude Max Subscription")
    lines.append(f"")
    lines.append(f"**Generated:** {now.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append(f"**Subscription:** Claude Max (Boss Marc @Bossmarc747)")
    lines.append(f"**Tracking Hook:** {'✅ Active' if hook['hooked'] else '⚠️ Not installed (estimates only)'}")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")
    
    # === EXECUTIVE SUMMARY ===
    lines.append(f"## 📋 Executive Summary")
    lines.append(f"")
    lines.append(f"| Metric | All-Time | Today ({today}) |")
    lines.append(f"|--------|----------|------|")
    lines.append(f"| **API Calls (from logs)** | {total_api_calls:,} | {today_calls:,} |")
    lines.append(f"| **Cache Creation Tokens** | {fmt_tokens(total_cache_creation)} | {fmt_tokens(today_cc)} |")
    lines.append(f"| **Cache Read Tokens** | {fmt_tokens(total_cache_read)} | {fmt_tokens(today_cr)} |")
    lines.append(f"| **Cache Hit Rate** | {cache_hit:.1f}% | - |")
    lines.append(f"| **Message Tokens (content)** | {fmt_tokens(total_msg_tokens)} | - |")
    lines.append(f"| **Estimated Total Tokens** | {fmt_tokens(total_estimated)} | - |")
    lines.append(f"| **Chat Sessions** | {len(all_chats)} | - |")
    lines.append(f"| **Log Files Parsed** | {len(all_logs)} | {len(today_logs)} |")
    lines.append(f"")
    
    # === AGENT BREAKDOWN ===
    lines.append(f"## 🤖 Agent Breakdown")
    lines.append(f"")
    
    # Pareng Boyong
    lines.append(f"### Pareng Boyong (Agent Zero)")
    lines.append(f"- **Platform:** Docker container on VPS")
    lines.append(f"- **Model:** Claude Sonnet 4 / Opus 4 (via InnovateHub OAuth)")
    lines.append(f"- **Chat Sessions:** {len(all_chats)}")
    lines.append(f"- **Total API Calls (logged):** {total_api_calls:,}")
    lines.append(f"- **Cache Tokens:** {fmt_tokens(cache_total)} (creation: {fmt_tokens(total_cache_creation)}, read: {fmt_tokens(total_cache_read)})")
    lines.append(f"- **Message Content Tokens:** {fmt_tokens(total_msg_tokens)}")
    lines.append(f"- **Estimated Total Consumption:** {fmt_tokens(total_estimated)}")
    lines.append(f"- **Data Source:** HTML logs + chat.json analysis")
    if not hook["hooked"]:
        lines.append(f"- **⚠️ Note:** API hook not installed. Totals are estimates. Install hook for exact tracking.")
    lines.append(f"")
    
    # ClawdBot
    lines.append(f"### ClawdBot (@bossmarc_serverbot)")
    lines.append(f"- **Platform:** systemd service on VPS")
    lines.append(f"- **Status:** {clawdbot['status']}")
    for note in clawdbot.get("notes", []):
        lines.append(f"- **Info:** {note}")
    if clawdbot.get("usage"):
        lines.append(f"- **Usage Data Found:** {len(clawdbot['usage'])} entries")
    else:
        lines.append(f"- **⚠️ Note:** No direct token tracking found. Uses Claude Code which tracks via Anthropic dashboard.")
    lines.append(f"")
    
    # OpenClaw
    lines.append(f"### OpenClaw (@bossabossbot)")
    lines.append(f"- **Platform:** PM2 service on VPS")
    lines.append(f"- **Status:** {openclaw['status']}")
    for note in openclaw.get("notes", []):
        lines.append(f"- **Info:** {note}")
    if openclaw.get("usage"):
        lines.append(f"- **Usage Data Found:** {len(openclaw['usage'])} entries")
    else:
        lines.append(f"- **⚠️ Note:** No direct token tracking found. Uses Claude Code which tracks via Anthropic dashboard.")
    lines.append(f"")
    
    # === CHAT SESSION DETAILS ===
    lines.append(f"## 💬 Chat Session Details (Pareng Boyong)")
    lines.append(f"")
    lines.append(f"| Chat ID | Name | Messages | AI/User | Msg Tokens | Est. Total | Tool Calls | Cache (C/R) |")
    lines.append(f"|---------|------|----------|---------|------------|------------|------------|-------------|")
    
    for c in sorted(all_chats, key=lambda x: x.created_at, reverse=True):
        name = c.chat_name[:25] + ".." if len(c.chat_name) > 25 else c.chat_name
        cache_str = f"{fmt_tokens(c.cache_creation)}/{fmt_tokens(c.cache_read)}" if c.cache_creation or c.cache_read else "-"
        lines.append(f"| `{c.chat_id}` | {name} | {c.message_count} | {c.ai_messages}/{c.user_messages} | {fmt_tokens(c.total_message_tokens)} | {fmt_tokens(c.estimated_total)} | {c.tool_calls} | {cache_str} |")
    lines.append(f"")
    
    # === LOG FILE DETAILS ===
    lines.append(f"## 📁 Log File Analysis")
    lines.append(f"")
    lines.append(f"| Log File | Timestamp | API Calls | Cache Creation | Cache Read | Size |")
    lines.append(f"|----------|-----------|-----------|----------------|------------|------|")
    for l in sorted(all_logs, key=lambda x: x.get("timestamp", ""), reverse=True)[:20]:
        ts = l.get("timestamp", "?")[:16]
        sz = f"{l['file_size']/1024:.1f}KB"
        lines.append(f"| {l['file']} | {ts} | {l['api_calls']} | {fmt_tokens(l['total_cache_creation'])} | {fmt_tokens(l['total_cache_read'])} | {sz} |")
    if len(all_logs) > 20:
        lines.append(f"| ... | ... | ... | ... | ... | ... |")
        lines.append(f"| **({len(all_logs)} total log files)** | | | | | |")
    lines.append(f"")
    
    # === ESTIMATION METHODOLOGY ===
    lines.append(f"## 📐 Estimation Methodology")
    lines.append(f"")
    lines.append(f"### Data Sources & Reliability")
    lines.append(f"")
    lines.append(f"| Source | Data Available | Reliability | Notes |")
    lines.append(f"|--------|---------------|-------------|-------|")
    lines.append(f"| HTML Logs | Cache creation/read per API call | ✅ **Exact** | Directly from Anthropic API response |")
    lines.append(f"| chat.json | Per-message token count | ✅ **Exact** | Counted by framework tokenizer |")
    lines.append(f"| API Hook (JSONL) | Full input/output/cache per call | ✅ **Exact** | Requires hook installation |")
    lines.append(f"| Estimated Total | Calculated from above | ⚠️ **Estimate** | Includes system prompt & history overhead |")
    lines.append(f"")
    lines.append(f"### Estimation Formula")
    lines.append(f"")
    lines.append(f"```")
    lines.append(f"For each chat session with N AI responses:")
    lines.append(f"  system_overhead = N × {SYSTEM_PROMPT_TOKENS:,} tokens (system prompt)")
    lines.append(f"  tools_overhead  = N × {TOOL_DEFS_TOKENS:,}

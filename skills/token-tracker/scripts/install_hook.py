#!/usr/bin/env python3
"""
Install Token Tracking Hook into Agent Zero's LLM pipeline.

This script patches the Agent Zero framework to log exact token usage
from every API call into a JSONL file for precise tracking.

Usage:
    python3 install_hook.py          # Install the hook
    python3 install_hook.py --check   # Check if hook is installed
    python3 install_hook.py --remove  # Remove the hook
"""

import os, sys, re, shutil, json
from datetime import datetime, timezone

TRACKING_DIR = "/a0/tmp/token_tracking"
TRACKING_FILE = os.path.join(TRACKING_DIR, "usage_log.jsonl")
HOOK_MARKER = "# TOKEN_TRACKER_HOOK_START"
HOOK_END = "# TOKEN_TRACKER_HOOK_END"

# Files to search for the LLM call pipeline
CANDIDATE_FILES = [
    "/a0/python/helpers/innovatehub_claude.py",
    "/a0/python/helpers/llm.py",
    "/a0/python/helpers/chat.py",
]

HOOK_CODE = '''
# TOKEN_TRACKER_HOOK_START
# Injected by token-tracker skill for exact token usage logging
def token_tracker_hook(response_metadata, agent_name="pareng-boyong", model="", chat_id=""):
    """Log token usage from API response metadata."""
    import json, os
    from datetime import datetime, timezone
    tracking_file = "/a0/tmp/token_tracking/usage_log.jsonl"
    os.makedirs(os.path.dirname(tracking_file), exist_ok=True)
    try:
        usage = response_metadata.get("usage", response_metadata.get("token_usage", {}))
        if not usage and hasattr(response_metadata, "usage"):
            usage = response_metadata.usage
        if not usage:
            return
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent": agent_name,
            "model": model or response_metadata.get("model", "unknown"),
            "chat_id": chat_id,
            "input_tokens": getattr(usage, "input_tokens", 0) or usage.get("input_tokens", 0) or usage.get("prompt_tokens", 0),
            "output_tokens": getattr(usage, "output_tokens", 0) or usage.get("output_tokens", 0) or usage.get("completion_tokens", 0),
            "cache_creation_tokens": getattr(usage, "cache_creation_input_tokens", 0) or usage.get("cache_creation_input_tokens", 0),
            "cache_read_tokens": getattr(usage, "cache_read_input_tokens", 0) or usage.get("cache_read_input_tokens", 0),
            "total_tokens": 0,
            "source": "api_hook"
        }
        record["total_tokens"] = (record["input_tokens"] + record["output_tokens"] +
                                   record["cache_creation_tokens"] + record["cache_read_tokens"])
        with open(tracking_file, "a") as f:
            f.write(json.dumps(record) + "\\n")
    except Exception:
        pass  # Never break the main pipeline
# TOKEN_TRACKER_HOOK_END
'''


def find_hook_target():
    """Find the best file to inject the hook into."""
    for fp in CANDIDATE_FILES:
        if os.path.exists(fp):
            with open(fp) as f:
                content = f.read()
            # Look for LLM call patterns
            if any(p in content for p in ["cache", "response", "llm", "invoke", "ainvoke"]):
                return fp
    # Search more broadly
    for root, dirs, files in os.walk("/a0/python"):
        for fn in files:
            if fn.endswith(".py"):
                fp = os.path.join(root, fn)
                try:
                    with open(fp) as f:
                        content = f.read()
                    if "Cache:" in content and "tokens" in content:
                        return fp
                except Exception:
                    continue
    return None


def check_installed():
    """Check if hook is already installed."""
    for fp in CANDIDATE_FILES:
        if os.path.exists(fp):
            with open(fp) as f:
                if HOOK_MARKER in f.read():
                    return fp
    return None


def install():
    """Install the tracking hook."""
    os.makedirs(TRACKING_DIR, exist_ok=True)
    
    existing = check_installed()
    if existing:
        print("Hook already installed in: {}".format(existing))
        return True
    
    target = find_hook_target()
    if not target:
        print("ERROR: Could not find suitable file to inject hook.")
        print("Searched: {}".format(CANDIDATE_FILES))
        print("\nManual installation required. Add this to your LLM callback:")
        print(HOOK_CODE)
        return False
    
    # Backup
    backup = target + ".bak." + datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(target, backup)
    print("Backup: {}".format(backup))
    
    # Inject at the top of the file (after imports)
    with open(target) as f:
        content = f.read()
    
    # Find insertion point (after last import)
    lines = content.split("\n")
    insert_idx = 0
    for i, line in enumerate(lines):
        if line.startswith("import ") or line.startswith("from "):
            insert_idx = i + 1
    
    lines.insert(insert_idx, HOOK_CODE)
    
    with open(target, "w") as f:
        f.write("\n".join(lines))
    
    # Write status
    status = {
        "installed": True,
        "target_file": target,
        "backup_file": backup,
        "installed_at": datetime.now(timezone.utc).isoformat()
    }
    with open(os.path.join(TRACKING_DIR, "hook_status.json"), "w") as f:
        json.dump(status, f, indent=2)
    
    print("Hook installed in: {}".format(target))
    print("\nIMPORTANT: You need to call token_tracker_hook(response_metadata)")
    print("after each LLM API call for tracking to work.")
    print("\nTracking file: {}".format(TRACKING_FILE))
    return True


def remove():
    """Remove the tracking hook."""
    target = check_installed()
    if not target:
        print("Hook not found in any file.")
        return
    
    with open(target) as f:
        content = f.read()
    
    # Remove between markers
    pattern = re.compile(
        re.escape(HOOK_MARKER) + r".*?" + re.escape(HOOK_END),
        re.DOTALL
    )
    content = pattern.sub("", content)
    
    with open(target, "w") as f:
        f.write(content)
    
    print("Hook removed from: {}".format(target))


def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ["--check", "check"]:
            result = check_installed()
            if result:
                print("Hook is installed in: {}".format(result))
            else:
                print("Hook is NOT installed.")
        elif arg in ["--remove", "remove"]:
            remove()
        elif arg in ["--help", "help"]:
            print(__doc__)
        else:
            install()
    else:
        install()


if __name__ == "__main__":
    main()

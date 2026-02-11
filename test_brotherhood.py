#!/usr/bin/env python3
"""Test the Brotherhood Watchdog tool functionality"""

import subprocess
import json

print("=" * 60)
print("Testing Brotherhood Watchdog Tool for Pareng Boyong")
print("=" * 60)

# Test 1: Run the watchdog script directly
print("\n[Test 1] Running brotherhood-watchdog.sh status...")
result = subprocess.run(
    "/srv/scripts/brotherhood-watchdog.sh status",
    shell=True,
    capture_output=True,
    text=True,
    timeout=30
)
print(result.stdout)
if result.stderr:
    print("Errors:", result.stderr)

# Test 2: Run JSON output
print("\n[Test 2] Running brotherhood-watchdog.sh json...")
result = subprocess.run(
    "/srv/scripts/brotherhood-watchdog.sh json",
    shell=True,
    capture_output=True,
    text=True,
    timeout=30
)
try:
    data = json.loads(result.stdout)
    print(f"Timestamp: {data.get('timestamp', 'N/A')}")
    members = data.get('members', {})
    healthy_count = sum(1 for m in members.values() if m.get('running') and m.get('healthy'))
    print(f"Healthy members: {healthy_count}/{len(members)}")
    for name, status in members.items():
        icon = '✅' if status.get('running') and status.get('healthy') else '❌'
        print(f"  {icon} {name}")
except Exception as e:
    print(f"JSON parse error: {e}")
    print(result.stdout)

# Test 3: Check specific member
print("\n[Test 3] Checking specific member (bantay-bot)...")
result = subprocess.run(
    "/srv/scripts/brotherhood-watchdog.sh check bantay-bot",
    shell=True,
    capture_output=True,
    text=True,
    timeout=15
)
print(f"Result: {result.stdout.strip()}")

# Test 4: Test alert script exists
print("\n[Test 4] Checking telegram-alert.sh exists...")
result = subprocess.run(
    "ls -la /srv/scripts/telegram-alert.sh",
    shell=True,
    capture_output=True,
    text=True
)
print(result.stdout.strip() if result.returncode == 0 else "Not found")

print("\n" + "=" * 60)
print("Brotherhood Watchdog Tool Tests Complete!")
print("=" * 60)

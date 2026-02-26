#!/bin/bash
# =============================================================================
# VPS + Bot Health Check
# Quick overview of VPS and all bot statuses
# =============================================================================

SSH="/root/vps-ssh.sh"

echo "🏥 VPS Health Check"
echo "=================="

$SSH 'bash -s' << 'REMOTE'
echo "📍 Host: $(hostname)"
echo "⏰ Uptime: $(uptime -p)"
echo ""

echo "💾 Memory:"
free -h | grep -E "Mem:|Swap:"
echo ""

echo "💿 Disk:"
df -h / | tail -1 | awk '{print "  Used: " $3 " / " $2 " (" $5 ")"}'
echo ""

echo "📊 Load: $(cat /proc/loadavg | awk '{print $1, $2, $3}')"
echo ""

echo "🤖 Bot Status:"
for entry in "clawdbot:18789" "bossaboss:18796" "innocoder:18790" "innovatehubph:18795"; do
    name=${entry%%:*}
    port=${entry##*:}
    code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 http://localhost:$port/ 2>/dev/null)
    if [[ "$code" =~ ^[23] ]]; then
        echo "  ✅ $name (port $port) - HTTP $code"
    else
        echo "  ❌ $name (port $port) - HTTP $code"
    fi
done
echo ""

echo "🐕 Watchdog:"
systemctl is-active unified-watchdog.service 2>/dev/null | xargs -I{} echo "  Status: {}"
tail -3 /var/log/unified-watchdog-v2.log 2>/dev/null | sed 's/^/  /'
echo ""

echo "🔝 Top Processes (by memory):"
ps aux --sort=-%mem | head -6 | tail -5 | awk '{print "  " $1 " " $2 " " $4 "%mem " $11}'
REMOTE

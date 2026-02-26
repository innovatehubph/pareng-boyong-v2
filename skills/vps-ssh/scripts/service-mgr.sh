#!/bin/bash
# =============================================================================
# VPS Service Manager
# Usage: service-mgr.sh <action> <service>
# Actions: status, start, stop, restart, logs
# =============================================================================

SSH="/root/vps-ssh.sh"
ACTION="${1:-status}"
SERVICE="${2:-}"

# Known services mapping
declare -A SERVICES=(
    ["watchdog"]="unified-watchdog.service|system"
    ["clawdbot"]="clawdbot-gateway.service|user"
    ["bossaboss"]="openclaw-bossaboss.service|user"
    ["innocoder"]="openclaw-innocoder.service|user"
    ["innovatehubph"]="openclaw-innovatehubph.service|user"
    ["resource-watch"]="resource-watch.service|system"
)

if [ -z "$SERVICE" ]; then
    echo "Usage: $0 <action> <service>"
    echo "Actions: status, start, stop, restart, logs"
    echo "Services: ${!SERVICES[*]}"
    exit 1
fi

# Resolve service
ENTRY=${SERVICES[$SERVICE]}
if [ -z "$ENTRY" ]; then
    # Use as-is (raw service name)
    SVC_NAME="$SERVICE"
    SVC_TYPE="system"
else
    SVC_NAME=${ENTRY%%|*}
    SVC_TYPE=${ENTRY##*|}
fi

# Build systemctl command
if [ "$SVC_TYPE" = "user" ]; then
    SCTL="export XDG_RUNTIME_DIR=/run/user/0; export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/0/bus; systemctl --user"
else
    SCTL="systemctl"
fi

case "$ACTION" in
    status)
        $SSH "$SCTL status $SVC_NAME 2>/dev/null | head -15"
        ;;
    start|stop|restart)
        $SSH "$SCTL $ACTION $SVC_NAME 2>/dev/null && echo "✅ $SVC_NAME $ACTION successful" || echo "❌ $SVC_NAME $ACTION failed""
        ;;
    logs)
        if [ "$SVC_TYPE" = "user" ]; then
            $SSH "journalctl --user -u $SVC_NAME --no-pager -n 30 2>/dev/null"
        else
            $SSH "journalctl -u $SVC_NAME --no-pager -n 30 2>/dev/null"
        fi
        ;;
    *)
        echo "Unknown action: $ACTION"
        echo "Valid actions: status, start, stop, restart, logs"
        exit 1
        ;;
esac

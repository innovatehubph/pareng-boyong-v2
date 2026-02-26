#!/bin/bash
# =============================================================================
# VPS Direct SSH Command Executor
# Usage: /root/vps-ssh.sh "command to run on VPS"
# Or:    /root/vps-ssh.sh < script.sh  (pipe mode)
# =============================================================================

VPS_HOST="172.27.0.1"
SSH_KEY="/root/.ssh/id_ed25519_boyong"
SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=10 -o BatchMode=yes -o LogLevel=ERROR"

if [ -z "$1" ]; then
    # Read from stdin (pipe mode)
    ssh $SSH_OPTS -i "$SSH_KEY" root@"$VPS_HOST"
else
    # Execute command argument
    ssh $SSH_OPTS -i "$SSH_KEY" root@"$VPS_HOST" "$@"
fi

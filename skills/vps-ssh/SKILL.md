---
name: "vps-ssh"
description: "Execute commands directly on Boss Marc's VPS (srv970577) via SSH from inside the Docker container. Use this skill whenever you need to manage systemd services, restart bots, check logs, install packages, or run ANY command on the VPS host. Replaces the old cron workaround hack."
version: "1.0.0"
author: "Pareng Boyong"
tags: ["vps", "ssh", "server", "devops", "services", "systemd", "bots", "management"]
trigger_patterns:
  - "run on vps"
  - "execute on server"
  - "restart service"
  - "restart bot"
  - "check vps"
  - "vps command"
  - "server command"
  - "systemctl"
  - "manage service"
  - "vps health"
  - "server status"
  - "check bots"
  - "bot status"
---

# VPS SSH Direct Access

Execute commands directly on Boss Marc's VPS (srv970577) from inside the Pareng Boyong Docker container via SSH.

## Why This Exists

**Problem:** Pareng Boyong runs inside Docker. VPS commands (systemctl, pm2, etc.) can't run from inside the container.

**Old Hack:** Write a script to `/vps/root/`, add a cron entry, wait 60+ seconds, clean up artifacts. Fragile, slow, error-prone.

**This Skill:** Direct SSH to VPS host. Instant execution. No artifacts. Reliable.

## Connection Details

| Parameter | Value |
|-----------|-------|
| VPS Host IP (from Docker) | `172.27.0.1` |
| SSH Key | `/root/.ssh/id_ed25519_boyong` |
| SSH User | `root` |
| Helper Script | `/root/vps-ssh.sh` |
| VPS Hostname | `srv970577` |

## Quick Usage

### Method 1: Helper Script (Recommended)

```bash
# Single command
/root/vps-ssh.sh 'command here'

# Examples
/root/vps-ssh.sh 'hostname && uptime'
/root/vps-ssh.sh 'systemctl restart unified-watchdog.service'
/root/vps-ssh.sh 'free -h'
/root/vps-ssh.sh 'pm2 list'
```

### Method 2: Direct SSH

```bash
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 -o BatchMode=yes -o LogLevel=ERROR \
    -i /root/.ssh/id_ed25519_boyong root@172.27.0.1 'command'
```

### Method 3: Multi-line Commands

```bash
/root/vps-ssh.sh 'bash -s' << 'EOF'
echo "Running multiple commands..."
hostname
uptime
free -h
EOF
```

## Common Operations

### Service Management

```bash
# System services (systemd)
/root/vps-ssh.sh 'systemctl status unified-watchdog.service'
/root/vps-ssh.sh 'systemctl restart unified-watchdog.service'
/root/vps-ssh.sh 'systemctl stop some-service'
/root/vps-ssh.sh 'systemctl enable some-service'

# User services (OpenClaw bots)
/root/vps-ssh.sh 'export XDG_RUNTIME_DIR=/run/user/0; export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/0/bus; systemctl --user status clawdbot-gateway.service'
/root/vps-ssh.sh 'export XDG_RUNTIME_DIR=/run/user/0; export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/0/bus; systemctl --user restart openclaw-bossaboss.service'

# PM2 processes
/root/vps-ssh.sh 'pm2 list'
/root/vps-ssh.sh 'pm2 restart bantay-bot'
```

### Health Checks

```bash
# Check all bot ports
/root/vps-ssh.sh 'for p in 18789 18790 18795 18796; do echo -n "Port $p: "; curl -s -o /dev/null -w "%{http_code}" --max-time 3 http://localhost:$p/; echo; done'

# System health
/root/vps-ssh.sh 'echo "=== MEMORY ==="; free -h; echo ""; echo "=== DISK ==="; df -h /; echo ""; echo "=== LOAD ==="; uptime; echo ""; echo "=== TOP CPU ==="; ps aux --sort=-%cpu | head -6'
```

### Log Checking

```bash
# Watchdog logs
/root/vps-ssh.sh 'tail -20 /var/log/unified-watchdog-v2.log'

# System logs
/root/vps-ssh.sh 'journalctl -u unified-watchdog.service --no-pager -n 20'

# Bot logs
/root/vps-ssh.sh 'journalctl --user -u clawdbot-gateway.service --no-pager -n 20'
```

### File Operations

```bash
# Read files
/root/vps-ssh.sh 'cat /srv/apps/unified-watchdog/watchdog.sh'

# Edit files (use /vps mount for writing, SSH for verification)
# Write via: open('/vps/path/to/file', 'w')
# Verify via: /root/vps-ssh.sh 'cat /path/to/file'
```

## Hybrid Workflow (Best Practice)

Combine filesystem mount + SSH for optimal workflow:

1. **Write files** → Use `/vps/` mount (Python `open()` or terminal `cat >`)
2. **Restart services** → Use SSH (`/root/vps-ssh.sh 'systemctl restart ...''`)
3. **Check results** → Use SSH (`/root/vps-ssh.sh 'tail -f /var/log/...''`)

```python
# Example: Deploy and restart
with open('/vps/srv/apps/myapp/config.json', 'w') as f:
    f.write(new_config)

import subprocess
result = subprocess.run('/root/vps-ssh.sh "systemctl restart myapp"',
                        shell=True, capture_output=True, text=True)
print(result.stdout)
```

## Bot Reference

| Bot | Telegram Handle | Port | Service |
|-----|----------------|------|---------|
| Clawdbot | @bossmarc_serverbot | 18789 | clawdbot-gateway.service |
| Bossaboss | @bossabossbot | 18796 | openclaw-bossaboss.service |
| Innocoder | @innocoderbot | 18790 | openclaw-innocoder.service |
| InnovateHubPH | @innovatehubph_bot | 18795 | openclaw-innovatehubph.service |

## Troubleshooting

### SSH Connection Refused
```bash
# Check if SSH key exists
ls -la /root/.ssh/id_ed25519_boyong

# Check if key is in VPS authorized_keys
grep "boyong-vps-access" /vps/root/.ssh/authorized_keys

# If missing, add it:
ssh-keygen -y -f /root/.ssh/id_ed25519_boyong >> /vps/root/.ssh/authorized_keys
```

### SSH Timeout
```bash
# Verify gateway IP
cat /proc/net/route | awk '$2 == "00000000" {print $3}'
# Convert hex gateway to IP and update /root/vps-ssh.sh if changed
```

### Permission Denied
```bash
# Regenerate key pair if needed
ssh-keygen -t ed25519 -f /root/.ssh/id_ed25519_boyong -N "" -C "boyong-vps-access"
ssh-keygen -y -f /root/.ssh/id_ed25519_boyong >> /vps/root/.ssh/authorized_keys
```

## Setup Script

If SSH access is not working, run the setup script:
```bash
bash /a0/skills/vps-ssh/scripts/setup.sh
```

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/vps-ssh.sh` | Main SSH helper (also installed at `/root/vps-ssh.sh`) |
| `scripts/setup.sh` | Setup/verify SSH access |
| `scripts/health-check.sh` | Quick VPS + bot health check |
| `scripts/service-mgr.sh` | Service management helper |

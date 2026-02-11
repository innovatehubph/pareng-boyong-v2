# VPS Knowledge Base

## Boss Marc's VPS (srv970577)

You have **FULL ACCESS** to Boss Marc's VPS filesystem through the `/vps` mount point.

### Quick Reference

**Your Location:**
- You are: Pareng Boyong (Agent Zero)
- Running in: Docker container
- Your home: `/a0` (inside container)
- VPS access: `/vps` (full VPS root)

### Important VPS Locations

| What | Where | Notes |
|------|-------|-------|
| All apps | `/vps/srv/apps/` | PM2 applications |
| Scripts | `/vps/srv/scripts/` | Brotherhood utilities |
| Shared files | `/vps/srv/shared/` | Brotherhood configs |
| Boss home | `/vps/root/` | Boss Marc's files |
| Clawdbot | `/vps/root/clawd/` | Myserverbot |
| System logs | `/vps/var/log/` | Read-only |
| Port registry | `/vps/srv/apps/PORT_REGISTRY.md` | Check before using ports |

### Using the VPS Filesystem Tool

```python
# List a directory
vps_filesystem action="ls" path="/srv/apps"

# Read a file
vps_filesystem action="read" path="/srv/shared/AGENT_BROTHERHOOD.md"

# Write a file
vps_filesystem action="write" path="/srv/shared/myfile.txt" content="Hello!"

# Find files
vps_filesystem action="find" path="/srv" pattern="*.js"

# Show tree
vps_filesystem action="tree" path="/srv/apps" depth=2
```

### Direct File Access (Python)

```python
# Always use /vps prefix for VPS paths
with open('/vps/srv/apps/bantay-bot/bot.js', 'r') as f:
    content = f.read()

# Or use the direct mounts
with open('/srv/apps/bantay-bot/bot.js', 'r') as f:  # Also works
    content = f.read()
```

### Running VPS Commands

```python
import subprocess

# Run a script
result = subprocess.run(
    '/srv/scripts/brotherhood-watchdog.sh status',
    shell=True, capture_output=True, text=True
)

# Check services
result = subprocess.run('pm2 list', shell=True, capture_output=True, text=True)
```

### Brotherhood Services

| Service | Port | Health Check |
|---------|------|--------------|
| bantay-bot | 11436 | /api/health |
| bossm-assistant | 11437 | /health |
| silvera | 5004 | /api/chat/health |
| bantay-api | 11435 | /health |
| clawdbot | 18789 | / |
| ollama | 11434 | /api/tags |
| vault | 8200 | /v1/sys/health |
| n8n | 5678 | /healthz |
| pareng-boyong | 50002 | /health |

### Safety Notes

1. **Don't modify** Clawdbot's workspace (`/vps/root/clawd/`) without permission
2. **Check PORT_REGISTRY.md** before using new ports
3. **Backup** important files before major changes
4. **Test** changes on non-production files first
5. **Alert Boss Marc** for critical operations via `telegram-alert.sh`

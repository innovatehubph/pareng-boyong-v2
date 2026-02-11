"""
Brotherhood Watchdog Tool for Pareng Boyong
Monitors and manages all AI Brotherhood members on Boss Marc's VPS

This tool allows Pareng Boyong to:
- Check status of all Brotherhood members
- Send alerts to Boss Marc when members are unhealthy
- Request fixes through the alert system

Created: 2026-02-03
Authority: Boss Marc (@Bossmarc747)

Note: Since Pareng Boyong runs in Docker and many services bind to 127.0.0.1,
health checks are performed via the host's watchdog script when possible.
"""

import subprocess
import json
import urllib.request
import urllib.error
from datetime import datetime
from python.helpers.tool import Tool, Response


# Docker gateway IP for services that bind to 0.0.0.0
DOCKER_GATEWAY = '172.20.0.1'

# Brotherhood member registry
# accessible_from_docker: True if service binds to 0.0.0.0
BROTHERHOOD_MEMBERS = {
    'clawdbot': {
        'type': 'systemd-user',
        'service': 'clawdbot-gateway.service',
        'description': 'Myserverbot (@bossmarc_serverbot)',
        'health_url': f'http://{DOCKER_GATEWAY}:18789/',
        'host_url': 'http://127.0.0.1:18789/',
        'accessible_from_docker': False  # binds to 127.0.0.1
    },
    'openclaw': {
        'type': 'systemd-user',
        'service': 'openclaw-gateway.service',
        'description': 'InnoCoderBot (@innocoder_bot)',
        'health_url': f'http://{DOCKER_GATEWAY}:18790/',
        'host_url': 'http://127.0.0.1:18790/',
        'accessible_from_docker': False  # binds to 127.0.0.1
    },
    'ollama': {
        'type': 'systemd',
        'service': 'ollama',
        'description': 'Local AI Engine (Bantay Brain)',
        'health_url': f'http://{DOCKER_GATEWAY}:11434/api/tags',
        'host_url': 'http://127.0.0.1:11434/api/tags',
        'accessible_from_docker': False  # binds to 127.0.0.1
    },
    'vault': {
        'type': 'systemd',
        'service': 'vault',
        'description': 'HashiCorp Vault (Secrets)',
        'health_url': f'http://{DOCKER_GATEWAY}:8200/v1/sys/health',
        'host_url': 'http://127.0.0.1:8200/v1/sys/health',
        'accessible_from_docker': False  # binds to 127.0.0.1
    },
    'bantay-bot': {
        'type': 'pm2',
        'service': 'bantay-bot',
        'description': 'Bantay AI (@innovatehubph_bot)',
        'health_url': f'http://{DOCKER_GATEWAY}:11436/api/health',
        'host_url': 'http://127.0.0.1:11436/api/health',
        'accessible_from_docker': True  # binds to 0.0.0.0
    },
    'bossm-assistant': {
        'type': 'pm2',
        'service': 'bossm-assistant',
        'description': 'BossM Assistant (@bossabossbot)',
        'health_url': f'http://{DOCKER_GATEWAY}:11437/health',
        'host_url': 'http://127.0.0.1:11437/health',
        'accessible_from_docker': False  # binds to 127.0.0.1
    },
    'bantay-api': {
        'type': 'pm2',
        'service': 'bantay-api',
        'description': 'Bantay REST API',
        'health_url': f'http://{DOCKER_GATEWAY}:11435/health',
        'host_url': 'http://127.0.0.1:11435/health',
        'accessible_from_docker': False  # likely binds to 127.0.0.1
    },
    'silvera': {
        'type': 'pm2',
        'service': 'silvera',
        'description': 'Silvera App',
        'health_url': f'http://{DOCKER_GATEWAY}:5004/api/chat/health',
        'host_url': 'http://127.0.0.1:5004/api/chat/health',
        'accessible_from_docker': True  # binds to 0.0.0.0
    },
    'pareng-boyong': {
        'type': 'docker',
        'service': 'pareng-boyong',
        'description': 'Pareng Boyong - Agent Zero (This is me!)',
        'health_url': 'http://127.0.0.1:80/health',  # Internal check
        'host_url': 'http://127.0.0.1:50002/health',
        'accessible_from_docker': True  # internal check
    },
    'n8n': {
        'type': 'docker',
        'service': 'n8n',
        'description': 'n8n Workflow Automation',
        'health_url': f'http://{DOCKER_GATEWAY}:5678/healthz',
        'host_url': 'http://127.0.0.1:5678/healthz',
        'accessible_from_docker': True  # Docker publishes to 0.0.0.0
    }
}


class BrotherhoodWatchdog(Tool):
    """
    Brotherhood Watchdog - Mutual monitoring system for AI Brotherhood members.

    Actions:
    - status: Show health status of all members
    - alert: Send alert to Boss Marc via Telegram
    - health: Quick health check of a specific member
    - list: List all Brotherhood members
    - fix: Request fix for a member (sends alert and triggers watchdog)
    """

    async def execute(self, **kwargs) -> Response:
        action = self.args.get("action", "status").lower()
        member = self.args.get("member", "").lower()
        message = self.args.get("message", "")

        try:
            if action == "status":
                return await self._get_status()
            elif action == "health":
                return await self._check_health(member)
            elif action == "alert":
                return await self._send_alert(message)
            elif action == "fix":
                return await self._request_fix(member)
            elif action == "list":
                return await self._list_members()
            else:
                return Response(
                    message=f"""Unknown action: {action}

Available actions:
- status: Show health status of all Brotherhood members
- health: Quick health check (use member="bantay-bot")
- alert: Send alert to Boss Marc (use message="your message")
- fix: Request fix for a member (triggers watchdog daemon)
- list: List all Brotherhood members

Examples:
- brotherhood_watchdog action="status"
- brotherhood_watchdog action="health" member="clawdbot"
- brotherhood_watchdog action="alert" message="Test alert from Pareng Boyong"
- brotherhood_watchdog action="fix" member="bantay-bot"
""",
                    break_loop=False
                )
        except Exception as e:
            return Response(
                message=f"Brotherhood Watchdog Error: {str(e)}",
                break_loop=False
            )

    def _run_host_check(self, member: str = None) -> dict:
        """Run the watchdog script to get status from host perspective"""
        try:
            if member:
                cmd = f"/srv/scripts/brotherhood-watchdog.sh check {member} 2>&1"
            else:
                cmd = "/srv/scripts/brotherhood-watchdog.sh json 2>&1"

            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )

            if member:
                # Single member check returns OK or error
                return {'healthy': result.stdout.strip() == 'OK', 'output': result.stdout.strip()}
            else:
                # JSON output for all members
                try:
                    return json.loads(result.stdout)
                except:
                    return {'error': result.stdout + result.stderr}

        except Exception as e:
            return {'error': str(e)}

    def _check_url(self, url: str, timeout: int = 5) -> tuple:
        """Check if a URL is responding. Returns (healthy, response_or_error)"""
        try:
            req = urllib.request.Request(url, method='GET')
            req.add_header('User-Agent', 'ParengBoyong-Brotherhood/1.0')
            with urllib.request.urlopen(req, timeout=timeout) as response:
                data = response.read().decode('utf-8')
                return (True, data[:200])
        except urllib.error.HTTPError as e:
            if e.code in [401, 403, 503]:
                return (True, f"HTTP {e.code}")
            return (False, f"HTTP {e.code}: {e.reason}")
        except urllib.error.URLError as e:
            return (False, f"Connection failed: {e.reason}")
        except Exception as e:
            return (False, str(e))

    async def _get_status(self) -> Response:
        """Get health status of all Brotherhood members"""
        status_report = "🤝 **Brotherhood Status Report**\n\n"

        # Get status from watchdog script (runs on host filesystem via mount)
        host_status = self._run_host_check()

        healthy_count = 0
        unhealthy_members = []

        if 'error' in host_status:
            # Fallback to direct checks for accessible services
            status_report += "_Note: Host watchdog unavailable, using direct checks_\n\n"

            for name, info in BROTHERHOOD_MEMBERS.items():
                if info.get('accessible_from_docker', False):
                    healthy, _ = self._check_url(info['health_url'])
                    if healthy:
                        healthy_count += 1
                        icon = '✅'
                    else:
                        icon = '❌'
                        unhealthy_members.append(name)
                else:
                    icon = '❓'  # Unknown - can't check from Docker

                status_report += f"{icon} **{name}** - {info['description']}\n"
        else:
            # Parse watchdog JSON output (has nested 'members' key)
            members_data = host_status.get('members', host_status)
            for name, info in BROTHERHOOD_MEMBERS.items():
                member_status = members_data.get(name, {})
                running = member_status.get('running', False)
                healthy = member_status.get('healthy', False)

                if running and healthy:
                    healthy_count += 1
                    icon = '✅'
                else:
                    icon = '❌'
                    unhealthy_members.append(name)

                status_report += f"{icon} **{name}** - {info['description']}\n"

        total = len(BROTHERHOOD_MEMBERS)
        status_report += f"\n📊 **Summary:** {healthy_count}/{total} healthy"
        status_report += f"\n_Timestamp: {self._get_timestamp()}_"

        if unhealthy_members:
            status_report += f"\n\n⚠️ **Unhealthy members:** {', '.join(unhealthy_members)}"
            status_report += "\n\nUse `brotherhood_watchdog action=\"fix\" member=\"[name]\"` to request a fix."
        else:
            status_report += "\n\n✨ All Brotherhood members are healthy!"

        return Response(message=status_report, break_loop=False)

    async def _check_health(self, member: str) -> Response:
        """Quick health check for a specific member"""
        if not member:
            return Response(
                message="Please specify a member to check. Use `brotherhood_watchdog action=\"list\"` to see available members.",
                break_loop=False
            )

        if member not in BROTHERHOOD_MEMBERS:
            return Response(
                message=f"Unknown member: {member}. Use `brotherhood_watchdog action=\"list\"` to see available members.",
                break_loop=False
            )

        member_info = BROTHERHOOD_MEMBERS[member]

        result = f"❤️ **Health Check: {member}**\n\n"
        result += f"**Type:** {member_info['type']}\n"
        result += f"**Service:** {member_info['service']}\n"
        result += f"**Description:** {member_info['description']}\n"
        result += f"**Health URL:** {member_info['host_url']}\n\n"

        # Try host watchdog first
        host_check = self._run_host_check(member)

        if 'error' not in host_check:
            healthy = host_check.get('healthy', False)
            if healthy:
                result += "**Status:** ✅ **HEALTHY**\n"
                result += "_Verified via host watchdog_"
            else:
                result += f"**Status:** ❌ **UNHEALTHY**\n"
                result += f"Output: `{host_check.get('output', 'Unknown')}`\n\n"
                result += f"Use `brotherhood_watchdog action=\"fix\" member=\"{member}\"` to request a fix."
        else:
            # Fallback to direct check if accessible
            if member_info.get('accessible_from_docker', False):
                healthy, response = self._check_url(member_info['health_url'])
                if healthy:
                    result += "**Status:** ✅ **HEALTHY**\n"
                    result += f"Response: `{response[:100]}`"
                else:
                    result += f"**Status:** ❌ **UNHEALTHY**\n"
                    result += f"Error: `{response}`\n\n"
                    result += f"Use `brotherhood_watchdog action=\"fix\" member=\"{member}\"` to request a fix."
            else:
                result += "**Status:** ❓ **UNKNOWN**\n"
                result += "_Service binds to localhost only - not accessible from Docker container._\n"
                result += "Use the Telegram bot /brotherhood command for accurate status."

        return Response(message=result, break_loop=False)

    async def _send_alert(self, message: str) -> Response:
        """Send alert to Boss Marc via Telegram"""
        if not message:
            message = "Test alert from Pareng Boyong Brotherhood tool"

        try:
            cmd = f'/srv/scripts/telegram-alert.sh "INFO" "[Pareng Boyong] {message}"'
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                return Response(
                    message=f"🔔 **Alert sent to Boss Marc!**\n\nMessage: {message}",
                    break_loop=False
                )
            else:
                return Response(
                    message=f"⚠️ Alert may not have been sent.\n\nOutput: {result.stdout + result.stderr}",
                    break_loop=False
                )
        except Exception as e:
            return Response(
                message=f"❌ Failed to send alert: {str(e)}",
                break_loop=False
            )

    async def _request_fix(self, member: str) -> Response:
        """Request a fix for a member by triggering the watchdog daemon"""
        if not member:
            return Response(
                message="Please specify a member to fix. Use `brotherhood_watchdog action=\"list\"` to see available members, or use member=\"all\".",
                break_loop=False
            )

        if member != "all" and member not in BROTHERHOOD_MEMBERS:
            return Response(
                message=f"Unknown member: {member}. Use `brotherhood_watchdog action=\"list\"` to see available members.",
                break_loop=False
            )

        try:
            # Send alert first
            alert_msg = f"Fix requested for {member} by Pareng Boyong"
            alert_cmd = f'/srv/scripts/telegram-alert.sh "WARNING" "[Pareng Boyong] {alert_msg}"'
            subprocess.run(alert_cmd, shell=True, capture_output=True, text=True, timeout=30)

            # Trigger the fix via watchdog script
            if member == "all":
                fix_cmd = "/srv/scripts/brotherhood-watchdog.sh fix 2>&1"
                target_desc = "all members"
            else:
                fix_cmd = f"/srv/scripts/brotherhood-watchdog.sh fix {member} 2>&1"
                member_info = BROTHERHOOD_MEMBERS[member]
                target_desc = f"{member} ({member_info['description']})"

            fix_result = subprocess.run(
                fix_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120
            )

            response = f"🔧 **Fix Requested: {target_desc}**\n\n"
            response += f"📢 Alert sent to Boss Marc\n"
            response += f"🔄 Watchdog fix triggered\n\n"

            output = (fix_result.stdout + fix_result.stderr)[-800:]
            if output.strip():
                response += f"**Output:**\n```\n{output}\n```\n"

            # Post-fix status check
            response += "\n**Post-fix Status:**\n"
            post_status = self._run_host_check()

            if 'error' not in post_status:
                members_data = post_status.get('members', post_status)
                if member == "all":
                    for name in BROTHERHOOD_MEMBERS:
                        status = members_data.get(name, {})
                        healthy = status.get('running', False) and status.get('healthy', False)
                        icon = '✅' if healthy else '❌'
                        response += f"{icon} {name}\n"
                else:
                    status = members_data.get(member, {})
                    healthy = status.get('running', False) and status.get('healthy', False)
                    icon = '✅' if healthy else '❌'
                    response += f"{icon} {member}\n"
            else:
                response += "_Could not verify status_\n"

            return Response(message=response, break_loop=False)

        except Exception as e:
            return Response(
                message=f"❌ Fix request failed: {str(e)}",
                break_loop=False
            )

    async def _list_members(self) -> Response:
        """List all Brotherhood members"""
        result = "🤝 **Brotherhood Members**\n\n"

        result += "**AI Agents:**\n"
        for name, info in BROTHERHOOD_MEMBERS.items():
            if info['type'] in ['systemd-user', 'docker'] or 'bot' in name or 'assistant' in name:
                result += f"- `{name}` - {info['description']}\n"

        result += "\n**Services:**\n"
        for name, info in BROTHERHOOD_MEMBERS.items():
            if info['type'] in ['systemd', 'pm2'] and 'bot' not in name and 'assistant' not in name:
                result += f"- `{name}` - {info['description']}\n"

        result += "\n**Usage:**\n"
        result += "- `brotherhood_watchdog action=\"status\"` - Check all health\n"
        result += "- `brotherhood_watchdog action=\"health\" member=\"[name]\"` - Check one\n"
        result += "- `brotherhood_watchdog action=\"fix\" member=\"[name]\"` - Request fix\n"
        result += "- `brotherhood_watchdog action=\"alert\" message=\"[msg]\"` - Alert Boss Marc\n"

        return Response(message=result, break_loop=False)

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S PHT")

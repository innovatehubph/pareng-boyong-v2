"""
Custom Tool: innovatehub_config
Description: Configuration assistant for InnovateHub Business Hub - manage Facebook integration, Back4App settings, and dashboard configuration
Created by: Pareng Boyong (Auto-generated)
"""

from python.helpers.tool import Tool, Response


class InnovatehubConfig(Tool):
    """
    Configuration assistant for InnovateHub Business Hub - manage Facebook integration, Back4App settings, and dashboard configuration
    
    Parameters:
        action (string): What to do: status, check_facebook, check_back4app, get_config, restart_dashboard, check_logs, verify_webhook
        detail (string): Additional detail for certain actions

    """

    async def execute(self, **kwargs) -> Response:
        # Extract parameters
        action = self.args.get("action", "")
        detail = self.args.get("detail", "")

        
        # Custom logic
        import subprocess
        import json

        SSH = "sshpass -p 'Bossmarc@747' ssh -o StrictHostKeyChecking=no root@72.61.113.227"

        action = action or "status"
        detail = detail or ""

        if action == "status":
            # Check if dashboard is running
            out = subprocess.run(f"{SSH} 'ss -tulpn | grep 3457' 2>/dev/null", shell=True, capture_output=True, text=True).stdout
            result = f"**InnovateHub Business Hub Status**\n\n"
            result += f"Dashboard running on port 3457: {out.strip() if out else 'NOT RUNNING'}\n\n"
            result += "**Businesses configured:**\n"
            result += "- PlataPay (ID: GTHxktOij6)\n"
            result += "- InnovateHub (ID: g3EFKft6Wj)\n\n"
            result += "**Parse Server:** https://parseapi.back4app.com\n"
            result += "**Webhook URL:** https://parseapi.back4app.com/facebook/webhook"
    
        elif action == "check_facebook":
            # Check Facebook credentials in Back4App
            out = subprocess.run(f"{SSH} 'curl -s -X GET \"https://parseapi.back4app.com/classes/FacebookConfig\" -H \"X-Parse-Application-Id: lOpBh4pgpWdiYJmAU4aXSNyYYY8d86hxH2hilkWN\" -H \"X-Parse-Master-Key: t78J6V3bHE18i0ZfTIqVIyLUxlLYdU0L1GZYJd4h\"' 2>/dev/null", shell=True, capture_output=True, text=True).stdout
            result = f"**Facebook Configuration in Back4App:**\n\n{out[:2000]}"
    
        elif action == "check_back4app":
            # Test Parse connection
            out = subprocess.run(f"{SSH} 'curl -s -X GET \"https://parseapi.back4app.com/serverInfo\" -H \"X-Parse-Application-Id: lOpBh4pgpWdiYJmAU4aXSNyYYY8d86hxH2hilkWN\" -H \"X-Parse-Master-Key: t78J6V3bHE18i0ZfTIqVIyLUxlLYdU0L1GZYJd4h\"' 2>/dev/null", shell=True, capture_output=True, text=True).stdout
            try:
                data = json.loads(out)
                result = f"**Back4App Connection Status:**\n\n"
                result += f"Server Version: {data.get('parseServerVersion', 'N/A')}\n"
                result += f"Host: {data.get('host', 'N/A')}"
            except:
                result = f"Back4App response:\n{out[:500]}"
        
        elif action == "get_config":
            # Get full config
            out = subprocess.run(f"{SSH} 'cat /root/innovatehub-hub/dashboard/src/config/parse.ts' 2>/dev/null", shell=True, capture_output=True, text=True).stdout
            result = f"**Dashboard Config (parse.ts):**\n\n{out}"
    
        elif action == "restart_dashboard":
            out = subprocess.run(f"{SSH} 'pkill -f dashboard-server && cd /root/innovatehub-hub && node dashboard-server.js &' 2>/dev/null", shell=True, capture_output=True, text=True).stdout
            result = f"**Restarting Dashboard...**\n{out}"
    
        elif action == "check_logs":
            # Get recent logs
            out = subprocess.run(f"{SSH} 'pm2 logs innovatehub-hub --lines 20 --nostream 2>/dev/null || journalctl -u node -n 20 2>/dev/null' 2>/dev/null", shell=True, capture_output=True, text=True).stdout
            result = f"**Recent Logs:**\n\n{out[:2000]}"
    
        elif action == "verify_webhook":
            # Test webhook endpoint
            out = subprocess.run(f"{SSH} 'curl -s -X GET \"https://parseapi.back4app.com/facebook/webhook?hub.mode=subscribe&hub.verify_token=innovatehub_verify_2024&hub.challenge=test\"' 2>/dev/null", shell=True, capture_output=True, text=True).stdout
            result = f"**Webhook Verification:**\n\nResponse: {out}"
    
        elif action == "list_businesses":
            out = subprocess.run(f"{SSH} 'curl -s -X GET \"https://parseapi.back4app.com/classes/Business\" -H \"X-Parse-Application-Id: lOpBh4pgpWdiYJmAU4aXSNyYYY8d86hxH2hilkWN\" -H \"X-Parse-Master-Key: t78J6V3bHE18i0ZfTIqVIyLUxlLYdU0L1GZYJd4h\"' 2>/dev/null", shell=True, capture_output=True, text=True).stdout
            result = f"**Businesses in Database:**\n\n{out[:2000]}"
    
        else:
            result = f"Unknown action: {action}"

        result = result or "No output"
        
        # Return response (modify as needed)
        return Response(
            message=result if 'result' in dir() else "Tool executed successfully",
            break_loop=False
        )

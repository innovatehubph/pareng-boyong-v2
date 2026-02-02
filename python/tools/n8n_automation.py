"""
n8n Automation Tool for Pareng Boyong
Allows managing and triggering n8n workflows
"""

import os
import json
import requests
from python.helpers.tool import Tool, Response


class N8nAutomation(Tool):
    """
    Tool to interact with n8n automation platform.
    Can list, trigger, and manage workflows.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_url = os.environ.get("N8N_BASE_URL", "http://localhost:5678")
        self.api_key = os.environ.get("N8N_API_KEY", "")
        self.headers = {
            "X-N8N-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }

    async def execute(self, **kwargs) -> Response:
        action = self.args.get("action", "list").lower()
        
        if not self.api_key:
            return Response(
                message="Error: N8N_API_KEY not configured. Set it in environment variables.",
                break_loop=False
            )
        
        try:
            if action == "list":
                return await self.list_workflows()
            elif action == "get":
                return await self.get_workflow()
            elif action == "trigger":
                return await self.trigger_workflow()
            elif action == "activate":
                return await self.activate_workflow()
            elif action == "deactivate":
                return await self.deactivate_workflow()
            elif action == "executions":
                return await self.list_executions()
            elif action == "status":
                return await self.get_execution_status()
            else:
                return Response(
                    message=f"Unknown action: {action}. Available: list, get, trigger, activate, deactivate, executions, status",
                    break_loop=False
                )
        except requests.exceptions.RequestException as e:
            return Response(
                message=f"n8n API Error: {str(e)}",
                break_loop=False
            )

    async def list_workflows(self) -> Response:
        """List all workflows."""
        active_only = self.args.get("active_only", False)
        
        url = f"{self.base_url}/api/v1/workflows"
        if active_only:
            url += "?active=true"
        
        response = requests.get(url, headers=self.headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        workflows = data.get("data", [])
        
        if not workflows:
            return Response(message="No workflows found.", break_loop=False)
        
        result = "**n8n Workflows:**\n\n"
        for wf in workflows:
            status = "✅ Active" if wf.get("active") else "⏸️ Inactive"
            result += f"- **{wf['name']}** ({status})\n"
            result += f"  ID: `{wf['id']}`\n"
            if wf.get("triggerCount"):
                result += f"  Triggers: {wf['triggerCount']}\n"
        
        result += f"\n*Total: {len(workflows)} workflows*"
        return Response(message=result, break_loop=False)

    async def get_workflow(self) -> Response:
        """Get details of a specific workflow."""
        workflow_id = self.args.get("workflow_id", "")
        
        if not workflow_id:
            return Response(message="Error: workflow_id is required", break_loop=False)
        
        url = f"{self.base_url}/api/v1/workflows/{workflow_id}"
        response = requests.get(url, headers=self.headers, timeout=30)
        response.raise_for_status()
        wf = response.json()
        
        nodes = wf.get("nodes", [])
        node_types = [n.get("type", "").replace("n8n-nodes-base.", "") for n in nodes]
        
        result = f"**Workflow: {wf['name']}**\n\n"
        result += f"- ID: `{wf['id']}`\n"
        result += f"- Status: {'✅ Active' if wf.get('active') else '⏸️ Inactive'}\n"
        result += f"- Nodes: {len(nodes)} ({', '.join(set(node_types))})\n"
        result += f"- Created: {wf.get('createdAt', 'N/A')}\n"
        result += f"- Updated: {wf.get('updatedAt', 'N/A')}\n"
        
        return Response(message=result, break_loop=False)

    async def trigger_workflow(self) -> Response:
        """Manually trigger a workflow execution."""
        workflow_id = self.args.get("workflow_id", "")
        data = self.args.get("data", {})
        
        if not workflow_id:
            return Response(message="Error: workflow_id is required", break_loop=False)
        
        url = f"{self.base_url}/api/v1/workflows/{workflow_id}/run"
        
        payload = {}
        if data:
            payload["data"] = data if isinstance(data, dict) else json.loads(data)
        
        response = requests.post(url, headers=self.headers, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        
        execution_id = result.get("executionId", result.get("id", "N/A"))
        
        return Response(
            message=f"✅ Workflow triggered successfully!\n\n- Execution ID: `{execution_id}`\n- Status: Running",
            break_loop=False
        )

    async def activate_workflow(self) -> Response:
        """Activate a workflow."""
        workflow_id = self.args.get("workflow_id", "")
        
        if not workflow_id:
            return Response(message="Error: workflow_id is required", break_loop=False)
        
        url = f"{self.base_url}/api/v1/workflows/{workflow_id}/activate"
        response = requests.post(url, headers=self.headers, timeout=30)
        response.raise_for_status()
        
        return Response(
            message=f"✅ Workflow `{workflow_id}` activated successfully!",
            break_loop=False
        )

    async def deactivate_workflow(self) -> Response:
        """Deactivate a workflow."""
        workflow_id = self.args.get("workflow_id", "")
        
        if not workflow_id:
            return Response(message="Error: workflow_id is required", break_loop=False)
        
        url = f"{self.base_url}/api/v1/workflows/{workflow_id}/deactivate"
        response = requests.post(url, headers=self.headers, timeout=30)
        response.raise_for_status()
        
        return Response(
            message=f"⏸️ Workflow `{workflow_id}` deactivated.",
            break_loop=False
        )

    async def list_executions(self) -> Response:
        """List recent workflow executions."""
        workflow_id = self.args.get("workflow_id", "")
        limit = self.args.get("limit", 10)
        
        url = f"{self.base_url}/api/v1/executions?limit={limit}"
        if workflow_id:
            url += f"&workflowId={workflow_id}"
        
        response = requests.get(url, headers=self.headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        executions = data.get("data", [])
        
        if not executions:
            return Response(message="No executions found.", break_loop=False)
        
        result = "**Recent Executions:**\n\n"
        for ex in executions[:limit]:
            status_icon = "✅" if ex.get("finished") and not ex.get("stoppedAt") else "❌" if ex.get("stoppedAt") else "⏳"
            result += f"- {status_icon} `{ex['id'][:8]}...` - {ex.get('workflowId', 'N/A')}\n"
            result += f"  Started: {ex.get('startedAt', 'N/A')}\n"
        
        return Response(message=result, break_loop=False)

    async def get_execution_status(self) -> Response:
        """Get status of a specific execution."""
        execution_id = self.args.get("execution_id", "")
        
        if not execution_id:
            return Response(message="Error: execution_id is required", break_loop=False)
        
        url = f"{self.base_url}/api/v1/executions/{execution_id}"
        response = requests.get(url, headers=self.headers, timeout=30)
        response.raise_for_status()
        ex = response.json()
        
        status = "✅ Completed" if ex.get("finished") else "❌ Failed" if ex.get("stoppedAt") else "⏳ Running"
        
        result = f"**Execution Status:**\n\n"
        result += f"- ID: `{ex['id']}`\n"
        result += f"- Status: {status}\n"
        result += f"- Workflow: {ex.get('workflowId', 'N/A')}\n"
        result += f"- Started: {ex.get('startedAt', 'N/A')}\n"
        if ex.get("stoppedAt"):
            result += f"- Stopped: {ex.get('stoppedAt')}\n"
        
        return Response(message=result, break_loop=False)

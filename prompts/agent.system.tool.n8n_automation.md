### n8n_automation:
**MANAGE AND TRIGGER n8n WORKFLOWS** - Control automation pipelines directly.
Use this tool to list workflows, trigger automations, check execution status, and manage workflow states.

**Actions:**
- `list` - List all workflows (use active_only=true for active only)
- `get` - Get workflow details
- `trigger` - Manually run a workflow (with optional data)
- `activate` - Activate a workflow
- `deactivate` - Deactivate a workflow
- `executions` - List recent executions
- `status` - Check execution status

### List all workflows:
~~~json
{
    "thoughts": ["Let me check what automations are available"],
    "headline": "Listing n8n workflows",
    "tool_name": "n8n_automation",
    "tool_args": {
        "action": "list"
    }
}
~~~

### List only active workflows:
~~~json
{
    "thoughts": ["Checking active automations"],
    "headline": "Listing active workflows",
    "tool_name": "n8n_automation",
    "tool_args": {
        "action": "list",
        "active_only": true
    }
}
~~~

### Get workflow details:
~~~json
{
    "thoughts": ["Let me see the details of this workflow"],
    "headline": "Getting workflow details",
    "tool_name": "n8n_automation",
    "tool_args": {
        "action": "get",
        "workflow_id": "abc123..."
    }
}
~~~

### Trigger a workflow:
~~~json
{
    "thoughts": ["I need to run this automation now"],
    "headline": "Triggering workflow",
    "tool_name": "n8n_automation",
    "tool_args": {
        "action": "trigger",
        "workflow_id": "abc123...",
        "data": {"key": "value"}
    }
}
~~~

### Check execution status:
~~~json
{
    "thoughts": ["Let me check if that execution completed"],
    "headline": "Checking execution status",
    "tool_name": "n8n_automation",
    "tool_args": {
        "action": "status",
        "execution_id": "exec123..."
    }
}
~~~

### Activate/Deactivate workflows:
~~~json
{
    "thoughts": ["Enabling this automation"],
    "headline": "Activating workflow",
    "tool_name": "n8n_automation",
    "tool_args": {
        "action": "activate",
        "workflow_id": "abc123..."
    }
}
~~~

**Available Workflows:**
- Silvera: Product AI Pipeline (generate descriptions, SEO, taglines)
- Silvera: Order Processing Pipeline (orders, inventory, emails)
- Silvera: Review Auto-Moderation (sentiment analysis)
- Silvera: Abandoned Cart Recovery (email sequences)
- 747 Live AI Customer Support (classify & respond)

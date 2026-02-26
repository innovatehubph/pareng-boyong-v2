### innovatehub_config:
Configuration assistant for InnovateHub Business Hub - manage Facebook integration, Back4App settings, and dashboard configuration

**Parameters:**
- action: (required) What to do: status, check_facebook, check_back4app, get_config, restart_dashboard, check_logs, verify_webhook
- detail: (optional) Additional detail for certain actions

usage:
~~~json
{
  "tool_name": "innovatehub_config",
  "tool_args": {
    "action": "status"
  }
}
~~~

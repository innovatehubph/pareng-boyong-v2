---
name: n8n-automation
description: Manage n8n workflows - list, activate, deactivate, and trigger workflow executions.
version: 1.0.0
author: InnovateHub
tags:
  - automation
  - n8n
  - workflow
  - integration
triggers:
  - n8n workflow
  - automation
  - trigger workflow
  - list workflows
allowed_tools:
  - code_execution_tool
---

# n8n Workflow Automation

Control n8n workflows programmatically.

## Configuration
- **Base URL:** `http://localhost:5678` (or configured N8N_BASE_URL)
- **API Key:** Set via N8N_API_KEY environment variable

## Usage

### List Workflows
```python
response = n8n_automation(action="list")
```

### Activate Workflow
```python
response = n8n_automation(
    action="activate",
    workflow_id="123"
)
```

### Trigger Workflow
```python
response = n8n_automation(
    action="trigger",
    workflow_id="123",
    data={"key": "value"}
)
```

### Get Executions
```python
response = n8n_automation(
    action="executions",
    workflow_id="123"
)
```

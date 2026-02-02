# Pareng Boyong Tool Creation Guide

## 📊 Tool System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     HOW PARENG BOYONG USES TOOLS                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. WHEN - System prompt includes tool descriptions                 │
│     ↓    (agent.system.tool.*.md files)                            │
│                                                                     │
│  2. WHAT - Agent outputs JSON with tool_name + tool_args            │
│     ↓    {"tool_name": "xxx", "tool_args": {...}}                  │
│                                                                     │
│  3. HOW  - extract_tools.py parses JSON, loads Python class         │
│     ↓    from python/tools/{tool_name}.py                          │
│                                                                     │
│  4. WHERE - Tool.execute() runs, returns Response                   │
│            Response added to conversation history                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## 📁 Files Needed to Create a New Tool

### Required Files (2 minimum):

| File | Location | Purpose |
|------|----------|---------|
| **Python Class** | `python/tools/{tool_name}.py` | Tool implementation |
| **Prompt File** | `prompts/agent.system.tool.{tool_name}.md` | Instructions for agent |

### Optional Files:

| File | Location | Purpose |
|------|----------|---------|
| **Response Prompt** | `prompts/fw.{tool_name}.response.md` | Custom response formatting |
| **Agent-specific** | `agents/{profile}/tools/{tool_name}.py` | Override for specific agent |
| **Agent-specific prompt** | `agents/{profile}/prompts/agent.system.tool.{tool_name}.md` | Agent-specific instructions |

---

## 🔧 Step-by-Step: Creating a New Tool

### Step 1: Create Python Class

**File:** `python/tools/my_new_tool.py`

```python
from python.helpers.tool import Tool, Response

class MyNewTool(Tool):
    """
    Your tool description here.
    """
    
    async def execute(self, **kwargs) -> Response:
        # Get arguments from self.args (parsed from JSON)
        param1 = self.args.get("param1", "default_value")
        param2 = self.args.get("param2", "")
        
        # Access agent context if needed
        # self.agent - the agent instance
        # self.agent.context - conversation context
        # self.agent.config - agent configuration
        
        # Do your tool logic here
        result = f"Processed: {param1}, {param2}"
        
        # Return response
        return Response(
            message=result,           # Text response for the agent
            break_loop=False,         # True = stop conversation, False = continue
            additional={"key": "val"} # Optional extra data
        )
    
    # Optional: Custom logging before execution
    async def before_execution(self, **kwargs):
        await super().before_execution(**kwargs)
        # Add custom pre-execution logic
    
    # Optional: Custom handling after execution
    async def after_execution(self, response: Response, **kwargs):
        await super().after_execution(response, **kwargs)
        # Add custom post-execution logic
```

### Step 2: Create Prompt File

**File:** `prompts/agent.system.tool.my_new_tool.md`

```markdown
### my_new_tool:
Brief description of what this tool does.
When to use it and any important notes.

**Parameters:**
- param1: (required) Description of param1
- param2: (optional) Description of param2, default: ""

usage:
~~~json
{
    "thoughts": [
        "I need to use my_new_tool because...",
        "The parameters I'll use are..."
    ],
    "headline": "Description of what I'm doing",
    "tool_name": "my_new_tool",
    "tool_args": {
        "param1": "value1",
        "param2": "value2"
    }
}
~~~
```

### Step 3: Restart Pareng Boyong

```bash
docker restart pareng-boyong
```

---

## 📚 Existing Tools Reference

### Core Tools:

| Tool | File | Purpose |
|------|------|---------|
| `response` | `response.py` | Final response to user |
| `code_execution` | `code_execution_tool.py` | Run Python/Node/Terminal |
| `call_subordinate` | `call_subordinate.py` | Create sub-agents |
| `memory_save` | `memory_save.py` | Save to long-term memory |
| `memory_load` | `memory_load.py` | Query memories |
| `memory_delete` | `memory_delete.py` | Delete specific memories |
| `memory_forget` | `memory_forget.py` | Forget by query |
| `search_engine` | `search_engine.py` | Web search |
| `document_query` | `document_query.py` | Query uploaded documents |
| `browser_agent` | `browser_agent.py` | Web browser automation |
| `scheduler` | `scheduler.py` | Schedule tasks |
| `notify_user` | `notify_user.py` | Send notifications |
| `input` | `input.py` | Request user input |
| `wait` | `wait.py` | Pause execution |
| `a2a_chat` | `a2a_chat.py` | Agent-to-Agent communication |
| `behaviour_adjustment` | `behaviour_adjustment.py` | Adjust agent behavior |
| `vision_load` | `vision_load.py` | Process images |

---

## 🎯 Tool Discovery Flow

```python
# From agent.py - process_tools()

1. Agent outputs JSON with tool request
2. extract_tools.json_parse_dirty(msg) parses the JSON
3. Tool name extracted from JSON

4. First, try agent-specific tools:
   classes = load_classes_from_file(
       f"agents/{profile}/tools/{name}.py", Tool
   )

5. If not found, try default tools:
   classes = load_classes_from_file(
       f"python/tools/{name}.py", Tool
   )

6. Instantiate tool and call execute()
7. Response added to history
```

---

## 🛠️ Tool Class Properties

Available in `self` within your tool:

| Property | Type | Description |
|----------|------|-------------|
| `self.agent` | Agent | The agent instance |
| `self.name` | str | Tool name |
| `self.args` | dict | Parsed arguments from JSON |
| `self.message` | str | Original message |
| `self.loop_data` | LoopData | Current execution loop data |

### Agent Properties (via `self.agent`):

| Property | Description |
|----------|-------------|
| `self.agent.config` | Agent configuration |
| `self.agent.context` | Conversation context |
| `self.agent.context.log` | Logging interface |
| `self.agent.data` | Shared data dict for tools |
| `self.agent.read_prompt()` | Read prompt templates |
| `self.agent.hist_add_*()` | Add to conversation history |

---

## 📝 Prompt Template Variables

Use in your tool prompts with `self.agent.read_prompt()`:

```python
result = self.agent.read_prompt(
    "fw.my_template.md",
    variable1="value1",
    variable2="value2"
)
```

Template file `prompts/fw.my_template.md`:
```markdown
Result: {{variable1}}
Details: {{variable2}}
```

---

## 🎪 Instruments (Alternative Approach)

Instruments are simpler, file-based tools for common tasks:

**Location:** `instruments/default/{instrument_name}/`

**Structure:**
```
instruments/default/my_instrument/
├── my_instrument.md      # Problem + Solution description
├── my_instrument.sh      # Shell script (optional)
└── my_instrument.py      # Python script (optional)
```

The agent uses code_execution tool to run instruments based on the .md description.

---

## ✅ Checklist for New Tools

- [ ] Create `python/tools/{tool_name}.py` with class extending `Tool`
- [ ] Implement `async def execute(self, **kwargs) -> Response`
- [ ] Create `prompts/agent.system.tool.{tool_name}.md` with usage example
- [ ] Include clear JSON example in prompt
- [ ] Test tool manually via chat
- [ ] Restart container after changes

---

## 🚀 Quick Start Template

Copy these files to create a new tool:

**1. python/tools/my_tool.py:**
```python
from python.helpers.tool import Tool, Response

class MyTool(Tool):
    async def execute(self, **kwargs) -> Response:
        # Your logic here
        result = self.args.get("input", "")
        return Response(message=f"Result: {result}", break_loop=False)
```

**2. prompts/agent.system.tool.my_tool.md:**
```markdown
### my_tool:
Description of the tool.

usage:
~~~json
{
    "thoughts": ["Using my_tool to..."],
    "headline": "Executing my_tool",
    "tool_name": "my_tool",
    "tool_args": {
        "input": "value"
    }
}
~~~
```

---

**Created:** 2026-02-02
**For:** Pareng Boyong v2
**By:** InnovateHub

### tool_creator:
**CREATE NEW TOOLS AUTONOMOUSLY** - This meta-tool lets you create, manage, and persist custom tools.
When you need a new capability that doesn't exist, CREATE IT using this tool.
Created tools persist across ALL sessions and become natively available.

**Actions:**
- `create` - Create a new tool (default)
- `list` - List all custom tools you've created
- `delete` - Delete a custom tool
- `view` - View source code of a tool

**Parameters for create:**
- tool_name: (required) lowercase, letters/numbers/underscores only, e.g. "web_scraper"
- description: (required) What the tool does
- parameters: (optional) List of parameter objects with: name, type, description, required, default, example
- python_code: (required) The actual Python logic (will be placed inside execute method)
- usage_example: (optional) Custom JSON usage example

**IMPORTANT:** In python_code, set `result` variable with the output string.

### Create a simple tool:
~~~json
{
    "thoughts": [
        "I need a tool to calculate fibonacci numbers",
        "Let me create it so I can use it in future sessions"
    ],
    "headline": "Creating fibonacci calculator tool",
    "tool_name": "tool_creator",
    "tool_args": {
        "action": "create",
        "tool_name": "fibonacci",
        "description": "Calculate fibonacci number at position n",
        "parameters": [
            {"name": "n", "type": "int", "description": "Position in fibonacci sequence", "required": true, "example": "10"}
        ],
        "python_code": "n = int(n) if n else 10\na, b = 0, 1\nfor _ in range(n):\n    a, b = b, a + b\nresult = f'Fibonacci({n}) = {a}'"
    }
}
~~~

### Create a tool with external API:
~~~json
{
    "thoughts": [
        "I need a tool to get weather data",
        "Creating it for future use"
    ],
    "headline": "Creating weather lookup tool",
    "tool_name": "tool_creator",
    "tool_args": {
        "action": "create",
        "tool_name": "weather_lookup",
        "description": "Get current weather for a city using wttr.in",
        "parameters": [
            {"name": "city", "type": "str", "description": "City name", "required": true, "example": "Manila"}
        ],
        "python_code": "import requests\nresponse = requests.get(f'https://wttr.in/{city}?format=3')\nresult = response.text if response.ok else f'Error: {response.status_code}'"
    }
}
~~~

### List all custom tools:
~~~json
{
    "thoughts": ["Let me see what custom tools I've created"],
    "headline": "Listing custom tools",
    "tool_name": "tool_creator",
    "tool_args": {
        "action": "list"
    }
}
~~~

### View a tool's source:
~~~json
{
    "thoughts": ["Let me check how fibonacci tool works"],
    "headline": "Viewing fibonacci tool source",
    "tool_name": "tool_creator",
    "tool_args": {
        "action": "view",
        "tool_name": "fibonacci"
    }
}
~~~

### Delete a custom tool:
~~~json
{
    "thoughts": ["I no longer need this tool"],
    "headline": "Deleting old tool",
    "tool_name": "tool_creator",
    "tool_args": {
        "action": "delete",
        "tool_name": "old_tool_name"
    }
}
~~~

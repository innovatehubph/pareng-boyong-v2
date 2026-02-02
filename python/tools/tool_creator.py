import os
import re
from python.helpers.tool import Tool, Response
from python.helpers.files import get_abs_path


class ToolCreator(Tool):
    """
    Meta-tool that allows Pareng Boyong to create new custom tools autonomously.
    Created tools persist across sessions and become natively available.
    """

    async def execute(self, **kwargs) -> Response:
        action = self.args.get("action", "create").lower()
        
        if action == "create":
            return await self.create_tool()
        elif action == "list":
            return await self.list_custom_tools()
        elif action == "delete":
            return await self.delete_tool()
        elif action == "view":
            return await self.view_tool()
        else:
            return Response(
                message=f"Unknown action: {action}. Use: create, list, delete, or view",
                break_loop=False
            )

    async def create_tool(self) -> Response:
        tool_name = self.args.get("tool_name", "").strip().lower()
        description = self.args.get("description", "").strip()
        parameters = self.args.get("parameters", [])
        python_code = self.args.get("python_code", "").strip()
        usage_example = self.args.get("usage_example", "").strip()
        
        # Validation
        if not tool_name:
            return Response(message="Error: tool_name is required", break_loop=False)
        
        if not re.match(r'^[a-z][a-z0-9_]*$', tool_name):
            return Response(
                message="Error: tool_name must be lowercase, start with letter, contain only letters/numbers/underscores",
                break_loop=False
            )
        
        if not description:
            return Response(message="Error: description is required", break_loop=False)
        
        if not python_code:
            return Response(message="Error: python_code is required", break_loop=False)
        
        # Check if tool already exists
        tool_path = get_abs_path(f"python/tools/{tool_name}.py")
        prompt_path = get_abs_path(f"prompts/agent.system.tool.{tool_name}.md")
        
        if os.path.exists(tool_path):
            return Response(
                message=f"Error: Tool '{tool_name}' already exists. Use action='delete' first to replace it.",
                break_loop=False
            )
        
        # Generate Python class
        class_name = ''.join(word.capitalize() for word in tool_name.split('_'))
        
        # Parse parameters for docstring
        param_docs = ""
        param_args = ""
        if parameters:
            for param in parameters:
                if isinstance(param, dict):
                    pname = param.get("name", "")
                    ptype = param.get("type", "str")
                    pdesc = param.get("description", "")
                    pdefault = param.get("default", "")
                    param_docs += f"        {pname} ({ptype}): {pdesc}\n"
                    if pdefault:
                        param_args += f'        {pname} = self.args.get("{pname}", {repr(pdefault)})\n'
                    else:
                        param_args += f'        {pname} = self.args.get("{pname}", "")\n'
        
        python_file_content = f'''"""
Custom Tool: {tool_name}
Description: {description}
Created by: Pareng Boyong (Auto-generated)
"""

from python.helpers.tool import Tool, Response


class {class_name}(Tool):
    """
    {description}
    
    Parameters:
{param_docs if param_docs else "        None"}
    """

    async def execute(self, **kwargs) -> Response:
        # Extract parameters
{param_args if param_args else "        pass"}
        
        # Custom logic
{self._indent_code(python_code, 8)}
        
        # Return response (modify as needed)
        return Response(
            message=result if 'result' in dir() else "Tool executed successfully",
            break_loop=False
        )
'''
        
        # Generate prompt file
        param_md = ""
        if parameters:
            param_md = "\n**Parameters:**\n"
            for param in parameters:
                if isinstance(param, dict):
                    pname = param.get("name", "")
                    pdesc = param.get("description", "")
                    preq = "required" if param.get("required", False) else "optional"
                    param_md += f"- {pname}: ({preq}) {pdesc}\n"
        
        # Generate usage example if not provided
        if not usage_example:
            example_args = {}
            if parameters:
                for param in parameters:
                    if isinstance(param, dict):
                        example_args[param.get("name", "")] = param.get("example", f"<{param.get('name', '')}>")
            
            usage_example = f'''{{
    "thoughts": [
        "I need to use {tool_name} to {description.lower()}",
    ],
    "headline": "Using {tool_name}",
    "tool_name": "{tool_name}",
    "tool_args": {self._format_dict(example_args)}
}}'''
        
        prompt_content = f'''### {tool_name}:
{description}
{param_md}
usage:
~~~json
{usage_example}
~~~
'''
        
        # Write files
        try:
            with open(tool_path, 'w') as f:
                f.write(python_file_content)
            
            with open(prompt_path, 'w') as f:
                f.write(prompt_content)
            
            # Log creation
            self.agent.context.log.log(
                type="info",
                heading=f"🔧 New Tool Created: {tool_name}",
                content=f"Python: {tool_path}\nPrompt: {prompt_path}"
            )
            
            return Response(
                message=f"""✅ **Tool '{tool_name}' created successfully!**

**Files created:**
- Python: `python/tools/{tool_name}.py`
- Prompt: `prompts/agent.system.tool.{tool_name}.md`

**The tool is now available for use in this and all future sessions.**

To use it, call:
```json
{{
    "tool_name": "{tool_name}",
    "tool_args": {{ ... }}
}}
```

Note: For complex tools, you may need to restart the container for changes to take full effect.""",
                break_loop=False
            )
            
        except Exception as e:
            return Response(
                message=f"Error creating tool: {str(e)}",
                break_loop=False
            )

    async def list_custom_tools(self) -> Response:
        """List all custom tools that have been created."""
        tools_dir = get_abs_path("python/tools")
        prompts_dir = get_abs_path("prompts")
        
        # Default tools that ship with Agent Zero
        default_tools = {
            'a2a_chat', 'behaviour_adjustment', 'browser_agent', 'call_subordinate',
            'code_execution_tool', 'document_query', 'input', 'memory_delete',
            'memory_forget', 'memory_load', 'memory_save', 'notify_user',
            'response', 'scheduler', 'search_engine', 'unknown', 'vision_load', 'wait',
            'tool_creator'  # This tool itself
        }
        
        custom_tools = []
        
        for filename in os.listdir(tools_dir):
            if filename.endswith('.py') and not filename.startswith('_'):
                tool_name = filename[:-3]  # Remove .py
                if tool_name not in default_tools:
                    # Check if it has a corresponding prompt
                    prompt_file = os.path.join(prompts_dir, f"agent.system.tool.{tool_name}.md")
                    has_prompt = os.path.exists(prompt_file)
                    custom_tools.append({
                        "name": tool_name,
                        "has_prompt": has_prompt,
                        "python_file": f"python/tools/{filename}",
                        "prompt_file": f"prompts/agent.system.tool.{tool_name}.md" if has_prompt else None
                    })
        
        if not custom_tools:
            return Response(
                message="No custom tools found. Use action='create' to create new tools.",
                break_loop=False
            )
        
        tools_list = "**Custom Tools:**\n\n"
        for tool in custom_tools:
            status = "✅" if tool["has_prompt"] else "⚠️ (missing prompt)"
            tools_list += f"- `{tool['name']}` {status}\n"
        
        return Response(message=tools_list, break_loop=False)

    async def delete_tool(self) -> Response:
        """Delete a custom tool."""
        tool_name = self.args.get("tool_name", "").strip().lower()
        
        if not tool_name:
            return Response(message="Error: tool_name is required for deletion", break_loop=False)
        
        # Protect default tools
        default_tools = {
            'a2a_chat', 'behaviour_adjustment', 'browser_agent', 'call_subordinate',
            'code_execution_tool', 'document_query', 'input', 'memory_delete',
            'memory_forget', 'memory_load', 'memory_save', 'notify_user',
            'response', 'scheduler', 'search_engine', 'unknown', 'vision_load', 'wait',
            'tool_creator'
        }
        
        if tool_name in default_tools:
            return Response(
                message=f"Error: Cannot delete default tool '{tool_name}'",
                break_loop=False
            )
        
        tool_path = get_abs_path(f"python/tools/{tool_name}.py")
        prompt_path = get_abs_path(f"prompts/agent.system.tool.{tool_name}.md")
        
        deleted = []
        
        if os.path.exists(tool_path):
            os.remove(tool_path)
            deleted.append(f"python/tools/{tool_name}.py")
        
        if os.path.exists(prompt_path):
            os.remove(prompt_path)
            deleted.append(f"prompts/agent.system.tool.{tool_name}.md")
        
        if deleted:
            return Response(
                message=f"✅ Tool '{tool_name}' deleted.\nRemoved: {', '.join(deleted)}",
                break_loop=False
            )
        else:
            return Response(
                message=f"Tool '{tool_name}' not found.",
                break_loop=False
            )

    async def view_tool(self) -> Response:
        """View the source code of a tool."""
        tool_name = self.args.get("tool_name", "").strip().lower()
        
        if not tool_name:
            return Response(message="Error: tool_name is required", break_loop=False)
        
        tool_path = get_abs_path(f"python/tools/{tool_name}.py")
        prompt_path = get_abs_path(f"prompts/agent.system.tool.{tool_name}.md")
        
        result = f"**Tool: {tool_name}**\n\n"
        
        if os.path.exists(tool_path):
            with open(tool_path, 'r') as f:
                result += f"**Python Code:**\n```python\n{f.read()}\n```\n\n"
        else:
            result += "Python file not found.\n\n"
        
        if os.path.exists(prompt_path):
            with open(prompt_path, 'r') as f:
                result += f"**Prompt:**\n```markdown\n{f.read()}\n```"
        else:
            result += "Prompt file not found."
        
        return Response(message=result, break_loop=False)

    def _indent_code(self, code: str, spaces: int) -> str:
        """Indent code block by specified spaces."""
        indent = ' ' * spaces
        lines = code.split('\n')
        return '\n'.join(indent + line if line.strip() else line for line in lines)
    
    def _format_dict(self, d: dict) -> str:
        """Format dictionary for JSON display."""
        if not d:
            return "{}"
        items = [f'        "{k}": "{v}"' for k, v in d.items()]
        return "{\n" + ",\n".join(items) + "\n    }"

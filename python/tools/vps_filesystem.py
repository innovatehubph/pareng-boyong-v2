"""
VPS Filesystem Tool for Pareng Boyong
Provides native access to Boss Marc's VPS filesystem from inside Docker

This tool allows Pareng Boyong to:
- Navigate and explore the VPS filesystem
- Read and write files on the VPS
- List directories and search for files
- Access all Brotherhood app directories

Created: 2026-02-03
Authority: Boss Marc (@Bossmarc747)

IMPORTANT: The VPS root is mounted at /vps inside this container.
All VPS paths should be prefixed with /vps when accessing from code.
"""

import os
import subprocess
import json
import glob as glob_module
from datetime import datetime
from pathlib import Path
from python.helpers.tool import Tool, Response


# VPS mount point inside Docker
VPS_ROOT = "/vps"

# Key VPS directories for quick access
VPS_PATHS = {
    'root': '/vps/root',
    'home': '/vps/root',
    'srv': '/vps/srv',
    'apps': '/vps/srv/apps',
    'scripts': '/vps/srv/scripts',
    'shared': '/vps/srv/shared',
    'clawd': '/vps/root/clawd',
    'logs': '/vps/var/log',
    'etc': '/vps/etc',
    'tmp': '/vps/tmp',
    # Direct mounts (also accessible without /vps prefix)
    'srv_direct': '/srv',
    'clawd_direct': '/clawd',
    'logs_direct': '/var/log',
    # Brotherhood apps
    'bantay-bot': '/vps/srv/apps/bantay-bot',
    'bossm-assistant': '/vps/srv/apps/bossm-assistant',
    'silvera': '/vps/srv/apps/silvera',
    'bantay-api': '/vps/srv/apps/bantay-api',
}


class VPSFilesystem(Tool):
    """
    VPS Filesystem - Native access to the VPS filesystem from Docker.

    Actions:
    - ls: List directory contents
    - read: Read a file
    - write: Write to a file
    - find: Search for files by pattern
    - tree: Show directory tree structure
    - info: Get file/directory info
    - paths: Show available quick-access paths
    - exists: Check if path exists

    All paths should be VPS paths (e.g., /srv/apps/bantay-bot)
    They will be automatically translated to /vps/... internally.
    """

    async def execute(self, **kwargs) -> Response:
        action = self.args.get("action", "paths").lower()
        path = self.args.get("path", "")
        content = self.args.get("content", "")
        pattern = self.args.get("pattern", "*")
        depth = int(self.args.get("depth", 2))

        try:
            if action == "ls":
                return await self._list_directory(path)
            elif action == "read":
                return await self._read_file(path)
            elif action == "write":
                return await self._write_file(path, content)
            elif action == "find":
                return await self._find_files(path, pattern)
            elif action == "tree":
                return await self._show_tree(path, depth)
            elif action == "info":
                return await self._get_info(path)
            elif action == "paths":
                return await self._show_paths()
            elif action == "exists":
                return await self._check_exists(path)
            else:
                return Response(
                    message=self._get_help(),
                    break_loop=False
                )
        except Exception as e:
            return Response(
                message=f"VPS Filesystem Error: {str(e)}",
                break_loop=False
            )

    def _to_vps_path(self, path: str) -> str:
        """Convert a VPS path to the Docker-internal path"""
        if not path:
            return VPS_ROOT

        # Check for quick-access aliases
        if path in VPS_PATHS:
            return VPS_PATHS[path]

        # Handle paths that already have /vps prefix
        if path.startswith('/vps'):
            return path

        # Handle absolute paths - prefix with /vps
        if path.startswith('/'):
            # Don't double-prefix paths that are direct mounts
            if path.startswith('/srv') or path.startswith('/clawd') or path.startswith('/var/log'):
                return path  # These are directly mounted
            return f"/vps{path}"

        # Relative paths - treat as relative to VPS root
        return f"{VPS_ROOT}/{path}"

    def _to_display_path(self, internal_path: str) -> str:
        """Convert internal path back to VPS-style path for display"""
        if internal_path.startswith('/vps'):
            return internal_path[4:]  # Remove /vps prefix
        return internal_path

    async def _list_directory(self, path: str) -> Response:
        """List directory contents"""
        vps_path = self._to_vps_path(path)

        if not os.path.exists(vps_path):
            return Response(
                message=f"Directory not found: {self._to_display_path(vps_path)}",
                break_loop=False
            )

        if not os.path.isdir(vps_path):
            return Response(
                message=f"Not a directory: {self._to_display_path(vps_path)}",
                break_loop=False
            )

        entries = []
        try:
            for entry in sorted(os.listdir(vps_path)):
                full_path = os.path.join(vps_path, entry)
                if os.path.isdir(full_path):
                    entries.append(f"📁 {entry}/")
                elif os.path.islink(full_path):
                    entries.append(f"🔗 {entry}")
                elif os.access(full_path, os.X_OK):
                    entries.append(f"⚡ {entry}")
                else:
                    entries.append(f"📄 {entry}")
        except PermissionError:
            return Response(
                message=f"Permission denied: {self._to_display_path(vps_path)}",
                break_loop=False
            )

        result = f"📂 **{self._to_display_path(vps_path)}**\n\n"
        if entries:
            result += "\n".join(entries)
        else:
            result += "_Empty directory_"

        result += f"\n\n_{len(entries)} items_"

        return Response(message=result, break_loop=False)

    async def _read_file(self, path: str) -> Response:
        """Read file contents"""
        if not path:
            return Response(
                message="Please specify a file path to read.",
                break_loop=False
            )

        vps_path = self._to_vps_path(path)

        if not os.path.exists(vps_path):
            return Response(
                message=f"File not found: {self._to_display_path(vps_path)}",
                break_loop=False
            )

        if os.path.isdir(vps_path):
            return Response(
                message=f"Path is a directory, not a file: {self._to_display_path(vps_path)}",
                break_loop=False
            )

        try:
            # Check file size first
            size = os.path.getsize(vps_path)
            if size > 100000:  # 100KB limit
                return Response(
                    message=f"File too large ({size} bytes). Maximum is 100KB.\nPath: {self._to_display_path(vps_path)}",
                    break_loop=False
                )

            with open(vps_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()

            result = f"📄 **{self._to_display_path(vps_path)}**\n"
            result += f"_Size: {size} bytes_\n\n"
            result += f"```\n{content[:10000]}\n```"

            if len(content) > 10000:
                result += f"\n\n_...truncated ({len(content)} total characters)_"

            return Response(message=result, break_loop=False)

        except PermissionError:
            return Response(
                message=f"Permission denied: {self._to_display_path(vps_path)}",
                break_loop=False
            )
        except UnicodeDecodeError:
            return Response(
                message=f"Binary file (cannot display): {self._to_display_path(vps_path)}",
                break_loop=False
            )

    async def _write_file(self, path: str, content: str) -> Response:
        """Write content to a file"""
        if not path:
            return Response(
                message="Please specify a file path to write to.",
                break_loop=False
            )

        if not content:
            return Response(
                message="Please specify content to write.",
                break_loop=False
            )

        vps_path = self._to_vps_path(path)

        # Safety check - don't overwrite critical system files
        protected = ['/vps/etc/passwd', '/vps/etc/shadow', '/vps/etc/sudoers']
        if vps_path in protected:
            return Response(
                message=f"Cannot write to protected system file: {self._to_display_path(vps_path)}",
                break_loop=False
            )

        try:
            # Create parent directories if needed
            parent_dir = os.path.dirname(vps_path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)

            with open(vps_path, 'w', encoding='utf-8') as f:
                f.write(content)

            size = os.path.getsize(vps_path)

            return Response(
                message=f"✅ **File written successfully**\n\nPath: {self._to_display_path(vps_path)}\nSize: {size} bytes",
                break_loop=False
            )

        except PermissionError:
            return Response(
                message=f"Permission denied: {self._to_display_path(vps_path)}",
                break_loop=False
            )

    async def _find_files(self, path: str, pattern: str) -> Response:
        """Find files matching a pattern"""
        vps_path = self._to_vps_path(path) if path else VPS_ROOT

        if not os.path.exists(vps_path):
            return Response(
                message=f"Path not found: {self._to_display_path(vps_path)}",
                break_loop=False
            )

        search_pattern = os.path.join(vps_path, "**", pattern)
        matches = []

        try:
            for match in glob_module.glob(search_pattern, recursive=True):
                if len(matches) >= 50:  # Limit results
                    break
                display_path = self._to_display_path(match)
                if os.path.isdir(match):
                    matches.append(f"📁 {display_path}/")
                else:
                    matches.append(f"📄 {display_path}")
        except Exception as e:
            return Response(
                message=f"Search error: {str(e)}",
                break_loop=False
            )

        result = f"🔍 **Search Results**\n\n"
        result += f"Pattern: `{pattern}`\n"
        result += f"In: {self._to_display_path(vps_path)}\n\n"

        if matches:
            result += "\n".join(matches)
            if len(matches) >= 50:
                result += "\n\n_...results limited to 50 items_"
        else:
            result += "_No matches found_"

        return Response(message=result, break_loop=False)

    async def _show_tree(self, path: str, depth: int) -> Response:
        """Show directory tree structure"""
        vps_path = self._to_vps_path(path) if path else VPS_ROOT

        if not os.path.exists(vps_path):
            return Response(
                message=f"Path not found: {self._to_display_path(vps_path)}",
                break_loop=False
            )

        def build_tree(dir_path: str, prefix: str = "", current_depth: int = 0) -> list:
            if current_depth >= depth:
                return []

            lines = []
            try:
                entries = sorted(os.listdir(dir_path))
                dirs = [e for e in entries if os.path.isdir(os.path.join(dir_path, e))]
                files = [e for e in entries if not os.path.isdir(os.path.join(dir_path, e))]

                # Show directories first, then files
                all_entries = dirs + files
                for i, entry in enumerate(all_entries[:20]):  # Limit per directory
                    is_last = (i == len(all_entries) - 1) or (i == 19)
                    connector = "└── " if is_last else "├── "

                    full_path = os.path.join(dir_path, entry)
                    if os.path.isdir(full_path):
                        lines.append(f"{prefix}{connector}📁 {entry}/")
                        extension = "    " if is_last else "│   "
                        lines.extend(build_tree(full_path, prefix + extension, current_depth + 1))
                    else:
                        lines.append(f"{prefix}{connector}📄 {entry}")

                if len(all_entries) > 20:
                    lines.append(f"{prefix}    ... and {len(all_entries) - 20} more")

            except PermissionError:
                lines.append(f"{prefix}└── [Permission denied]")

            return lines

        result = f"🌳 **Directory Tree**\n\n"
        result += f"📂 {self._to_display_path(vps_path)}/\n"

        tree_lines = build_tree(vps_path)
        result += "\n".join(tree_lines) if tree_lines else "_Empty directory_"

        return Response(message=result, break_loop=False)

    async def _get_info(self, path: str) -> Response:
        """Get detailed file/directory information"""
        if not path:
            return Response(
                message="Please specify a path to get info for.",
                break_loop=False
            )

        vps_path = self._to_vps_path(path)

        if not os.path.exists(vps_path):
            return Response(
                message=f"Path not found: {self._to_display_path(vps_path)}",
                break_loop=False
            )

        try:
            stat = os.stat(vps_path)

            result = f"ℹ️ **Path Info**\n\n"
            result += f"**Path:** {self._to_display_path(vps_path)}\n"
            result += f"**Type:** {'Directory' if os.path.isdir(vps_path) else 'File'}\n"
            result += f"**Size:** {stat.st_size:,} bytes\n"
            result += f"**Permissions:** {oct(stat.st_mode)[-3:]}\n"
            result += f"**Owner UID:** {stat.st_uid}\n"
            result += f"**Group GID:** {stat.st_gid}\n"
            result += f"**Modified:** {datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}\n"
            result += f"**Accessed:** {datetime.fromtimestamp(stat.st_atime).strftime('%Y-%m-%d %H:%M:%S')}\n"

            if os.path.islink(vps_path):
                result += f"**Link Target:** {os.readlink(vps_path)}\n"

            return Response(message=result, break_loop=False)

        except PermissionError:
            return Response(
                message=f"Permission denied: {self._to_display_path(vps_path)}",
                break_loop=False
            )

    async def _show_paths(self) -> Response:
        """Show available quick-access paths"""
        result = "🗂️ **VPS Quick-Access Paths**\n\n"
        result += "_Use these aliases or full paths with any action._\n\n"

        result += "**System Paths:**\n"
        result += "- `root` → /root (Boss Marc's home)\n"
        result += "- `srv` → /srv (Services)\n"
        result += "- `apps` → /srv/apps (PM2 applications)\n"
        result += "- `scripts` → /srv/scripts (Utility scripts)\n"
        result += "- `shared` → /srv/shared (Brotherhood shared files)\n"
        result += "- `logs` → /var/log (System logs)\n"
        result += "- `etc` → /etc (Configuration)\n"
        result += "- `tmp` → /tmp (Temporary files)\n"

        result += "\n**Brotherhood Apps:**\n"
        result += "- `bantay-bot` → /srv/apps/bantay-bot\n"
        result += "- `bossm-assistant` → /srv/apps/bossm-assistant\n"
        result += "- `silvera` → /srv/apps/silvera\n"
        result += "- `bantay-api` → /srv/apps/bantay-api\n"
        result += "- `clawd` → /root/clawd (Myserverbot)\n"

        result += "\n**Usage Examples:**\n"
        result += "```\n"
        result += 'vps_filesystem action="ls" path="apps"\n'
        result += 'vps_filesystem action="read" path="/srv/apps/bantay-bot/package.json"\n'
        result += 'vps_filesystem action="find" path="apps" pattern="*.js"\n'
        result += 'vps_filesystem action="tree" path="shared" depth=2\n'
        result += "```"

        return Response(message=result, break_loop=False)

    async def _check_exists(self, path: str) -> Response:
        """Check if a path exists"""
        if not path:
            return Response(
                message="Please specify a path to check.",
                break_loop=False
            )

        vps_path = self._to_vps_path(path)
        exists = os.path.exists(vps_path)

        if exists:
            path_type = "directory" if os.path.isdir(vps_path) else "file"
            return Response(
                message=f"✅ **Path exists**\n\n{self._to_display_path(vps_path)}\nType: {path_type}",
                break_loop=False
            )
        else:
            return Response(
                message=f"❌ **Path does not exist**\n\n{self._to_display_path(vps_path)}",
                break_loop=False
            )

    def _get_help(self) -> str:
        """Return help message"""
        return """📁 **VPS Filesystem Tool**

Access the VPS filesystem natively from inside Docker.

**Actions:**
- `ls` - List directory contents
- `read` - Read a file
- `write` - Write to a file
- `find` - Search for files by pattern
- `tree` - Show directory tree
- `info` - Get file/directory info
- `paths` - Show quick-access paths
- `exists` - Check if path exists

**Parameters:**
- `path` - File/directory path (or alias like "apps")
- `content` - Content to write (for write action)
- `pattern` - Search pattern (for find action)
- `depth` - Tree depth (default: 2)

**Examples:**
```
vps_filesystem action="paths"
vps_filesystem action="ls" path="/srv/apps"
vps_filesystem action="read" path="/srv/shared/AGENT_BROTHERHOOD.md"
vps_filesystem action="tree" path="apps" depth=1
vps_filesystem action="find" path="apps" pattern="*.json"
vps_filesystem action="write" path="/srv/shared/test.txt" content="Hello!"
```

**Note:** VPS root is mounted at /vps. Paths like /srv work directly too."""

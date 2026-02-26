#!/usr/bin/env python3
"""
Notion Sync Example
===================
Sync data to Notion databases and pages using Composio.

Prerequisites:
- Notion connected in Composio dashboard
- COMPOSIO_API_KEY set in environment

Usage:
    python notion-sync.py list-databases
    python notion-sync.py create-page --database "Tasks" --title "New Task"
    python notion-sync.py sync-tasks --database "Tasks" --source tasks.json
"""

import os
import sys
import json
import argparse
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

def load_env():
    """Load environment variables from .env file."""
    env_path = os.path.join(os.path.dirname(__file__), '../../.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key, value)

load_env()

try:
    from composio import ComposioToolSet, App, Action
except ImportError:
    print("Error: composio package not installed")
    print("Install with: pip install composio-core")
    sys.exit(1)


class NotionSync:
    """Notion synchronization helper using Composio."""
    
    def __init__(self):
        """Initialize the sync helper."""
        self.toolset = ComposioToolSet()
        self._verify_connection()
        self._databases_cache = None
    
    def _verify_connection(self):
        """Verify Notion is connected."""
        try:
            connections = self.toolset.get_connected_accounts()
            notion_connected = any(
                c.app_name.lower() == "notion"
                for c in connections
            )
            
            if not notion_connected:
                print("⚠ Notion not connected")
                print("Connect at: https://app.composio.dev")
                sys.exit(1)
            
            print("✓ Notion connected")
        except Exception as e:
            print(f"⚠ Connection check failed: {e}")
    
    def list_databases(self):
        """
        List accessible Notion databases.
        
        Returns:
            List of databases
        """
        try:
            result = self.toolset.execute_action(
                action=Action.NOTION_SEARCH,
                params={
                    "filter": {"property": "object", "value": "database"}
                }
            )
            
            if result.get("error"):
                print(f"Error: {result['error']}")
                return []
            
            databases = result.get("data", {}).get("results", [])
            self._databases_cache = databases
            return databases
        
        except Exception as e:
            print(f"Error listing databases: {e}")
            return []
    
    def get_database_by_name(self, name):
        """
        Find a database by name.
        
        Args:
            name: Database name to search for
        
        Returns:
            Database object or None
        """
        if not self._databases_cache:
            self.list_databases()
        
        name_lower = name.lower()
        for db in self._databases_cache or []:
            title = db.get("title", [{}])
            if title:
                db_name = title[0].get("plain_text", "").lower()
                if db_name == name_lower or name_lower in db_name:
                    return db
        
        return None
    
    def query_database(self, database_id, filter_obj=None, sorts=None):
        """
        Query a Notion database.
        
        Args:
            database_id: Database ID
            filter_obj: Optional filter object
            sorts: Optional sort configuration
        
        Returns:
            List of pages/rows
        """
        params = {"database_id": database_id}
        
        if filter_obj:
            params["filter"] = filter_obj
        
        if sorts:
            params["sorts"] = sorts
        
        try:
            result = self.toolset.execute_action(
                action=Action.NOTION_QUERY_DATABASE,
                params=params
            )
            
            if result.get("error"):
                print(f"Error: {result['error']}")
                return []
            
            return result.get("data", {}).get("results", [])
        
        except Exception as e:
            print(f"Error querying database: {e}")
            return []
    
    def create_page(self, database_id, properties, content=None):
        """
        Create a page in a database.
        
        Args:
            database_id: Database ID
            properties: Page properties (matching database schema)
            content: Optional page content blocks
        
        Returns:
            Created page data or None
        """
        params = {
            "parent": {"database_id": database_id},
            "properties": properties
        }
        
        if content:
            params["children"] = content
        
        try:
            result = self.toolset.execute_action(
                action=Action.NOTION_CREATE_PAGE,
                params=params
            )
            
            if result.get("error"):
                print(f"Error: {result['error']}")
                return None
            
            return result.get("data", {})
        
        except Exception as e:
            print(f"Error creating page: {e}")
            return None
    
    def update_page(self, page_id, properties):
        """
        Update a page's properties.
        
        Args:
            page_id: Page ID
            properties: Properties to update
        
        Returns:
            Updated page data or None
        """
        try:
            result = self.toolset.execute_action(
                action=Action.NOTION_UPDATE_PAGE,
                params={
                    "page_id": page_id,
                    "properties": properties
                }
            )
            
            if result.get("error"):
                print(f"Error: {result['error']}")
                return None
            
            return result.get("data", {})
        
        except Exception as e:
            print(f"Error updating page: {e}")
            return None
    
    def append_blocks(self, page_id, blocks):
        """
        Append content blocks to a page.
        
        Args:
            page_id: Page ID
            blocks: List of block objects
        
        Returns:
            Success boolean
        """
        try:
            result = self.toolset.execute_action(
                action=Action.NOTION_APPEND_BLOCK_CHILDREN,
                params={
                    "block_id": page_id,
                    "children": blocks
                }
            )
            
            return not result.get("error")
        
        except Exception as e:
            print(f"Error appending blocks: {e}")
            return False


def format_database(db):
    """Format database for display."""
    title = db.get("title", [{}])
    name = title[0].get("plain_text", "Untitled") if title else "Untitled"
    db_id = db.get("id", "?")
    
    # Get properties
    props = db.get("properties", {})
    prop_names = list(props.keys())[:5]
    
    return f"📊 {name}\n   ID: {db_id}\n   Properties: {', '.join(prop_names)}"


def create_text_property(value):
    """Create a title/text property value."""
    return {
        "title": [{"text": {"content": value}}]
    }


def create_rich_text_property(value):
    """Create a rich text property value."""
    return {
        "rich_text": [{"text": {"content": value}}]
    }


def create_select_property(value):
    """Create a select property value."""
    return {"select": {"name": value}}


def create_checkbox_property(value):
    """Create a checkbox property value."""
    return {"checkbox": bool(value)}


def create_date_property(date_str):
    """Create a date property value."""
    return {"date": {"start": date_str}}


def create_paragraph_block(text):
    """Create a paragraph block."""
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{"type": "text", "text": {"content": text}}]
        }
    }


def create_heading_block(text, level=1):
    """Create a heading block."""
    heading_type = f"heading_{min(level, 3)}"
    return {
        "object": "block",
        "type": heading_type,
        heading_type: {
            "rich_text": [{"type": "text", "text": {"content": text}}]
        }
    }


def cmd_list_databases(args, sync):
    """List databases command."""
    print("\n📚 Notion Databases")
    print("=" * 60)
    
    databases = sync.list_databases()
    
    if not databases:
        print("No databases found.")
        print("Make sure Notion integration has access to your databases.")
        return
    
    for db in databases:
        print(format_database(db))
        print()
    
    print(f"Total: {len(databases)} database(s)")


def cmd_query(args, sync):
    """Query database command."""
    print(f"\n🔍 Querying: {args.database}")
    print("-" * 60)
    
    # Find database
    db = sync.get_database_by_name(args.database)
    if not db:
        # Try as ID
        db = {"id": args.database}
    
    db_id = db.get("id")
    
    # Query
    pages = sync.query_database(db_id)
    
    if not pages:
        print("No results found.")
        return
    
    print(f"Found {len(pages)} item(s):\n")
    
    for page in pages[:args.limit]:
        props = page.get("properties", {})
        
        # Try to get title
        title = "Untitled"
        for prop_name, prop_value in props.items():
            if prop_value.get("type") == "title":
                title_arr = prop_value.get("title", [])
                if title_arr:
                    title = title_arr[0].get("plain_text", "Untitled")
                break
        
        page_id = page.get("id", "?")[:8]
        print(f"  • {title} (id: {page_id}...)")


def cmd_create_page(args, sync):
    """Create page command."""
    print(f"\n➕ Creating page in: {args.database}")
    print("-" * 60)
    
    # Find database
    db = sync.get_database_by_name(args.database)
    if not db:
        print(f"Database '{args.database}' not found")
        return
    
    db_id = db.get("id")
    
    # Build properties
    # The title property name varies by database
    db_props = db.get("properties", {})
    title_prop = None
    for name, prop in db_props.items():
        if prop.get("type") == "title":
            title_prop = name
            break
    
    if not title_prop:
        title_prop = "Name"  # Common default
    
    properties = {
        title_prop: create_text_property(args.title)
    }
    
    # Add description if provided
    if args.description:
        # Find a rich_text property
        for name, prop in db_props.items():
            if prop.get("type") == "rich_text":
                properties[name] = create_rich_text_property(args.description)
                break
    
    # Create page
    page = sync.create_page(db_id, properties)
    
    if page:
        print(f"✓ Page created")
        print(f"  ID: {page.get('id')}")
        print(f"  URL: {page.get('url')}")
    else:
        print("✗ Failed to create page")


def cmd_sync_tasks(args, sync):
    """Sync tasks from JSON file command."""
    print(f"\n🔄 Syncing tasks to: {args.database}")
    print("-" * 60)
    
    # Load source file
    if not os.path.exists(args.source):
        print(f"Source file not found: {args.source}")
        return
    
    with open(args.source) as f:
        tasks = json.load(f)
    
    if not isinstance(tasks, list):
        tasks = [tasks]
    
    print(f"Found {len(tasks)} task(s) to sync")
    
    # Find database
    db = sync.get_database_by_name(args.database)
    if not db:
        print(f"Database '{args.database}' not found")
        return
    
    db_id = db.get("id")
    db_props = db.get("properties", {})
    
    # Find title property
    title_prop = "Name"
    for name, prop in db_props.items():
        if prop.get("type") == "title":
            title_prop = name
            break
    
    # Sync each task
    created = 0
    for task in tasks:
        title = task.get("title") or task.get("name") or "Untitled"
        
        properties = {
            title_prop: create_text_property(title)
        }
        
        # Map common fields
        if "status" in task and "Status" in db_props:
            properties["Status"] = create_select_property(task["status"])
        
        if "done" in task and "Done" in db_props:
            properties["Done"] = create_checkbox_property(task["done"])
        
        if "due" in task and "Due" in db_props:
            properties["Due"] = create_date_property(task["due"])
        
        if "description" in task:
            for name, prop in db_props.items():
                if prop.get("type") == "rich_text":
                    properties[name] = create_rich_text_property(task["description"])
                    break
        
        # Create the page
        page = sync.create_page(db_id, properties)
        if page:
            created += 1
            print(f"  ✓ {title}")
        else:
            print(f"  ✗ {title}")
    
    print(f"\nSynced {created}/{len(tasks)} task(s)")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Notion Sync")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # List databases command
    list_parser = subparsers.add_parser("list-databases", help="List databases")
    
    # Query command
    query_parser = subparsers.add_parser("query", help="Query database")
    query_parser.add_argument("--database", "-d", required=True, help="Database name or ID")
    query_parser.add_argument("--limit", "-l", type=int, default=10, help="Max results")
    
    # Create page command
    create_parser = subparsers.add_parser("create-page", help="Create page")
    create_parser.add_argument("--database", "-d", required=True, help="Database name or ID")
    create_parser.add_argument("--title", "-t", required=True, help="Page title")
    create_parser.add_argument("--description", help="Page description")
    
    # Sync tasks command
    sync_parser = subparsers.add_parser("sync-tasks", help="Sync tasks from JSON")
    sync_parser.add_argument("--database", "-d", required=True, help="Database name")
    sync_parser.add_argument("--source", "-s", required=True, help="Source JSON file")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    print("=" * 60)
    print("📝 Notion Sync")
    print("=" * 60)
    
    sync = NotionSync()
    
    commands = {
        "list-databases": cmd_list_databases,
        "query": cmd_query,
        "create-page": cmd_create_page,
        "sync-tasks": cmd_sync_tasks
    }
    
    commands[args.command](args, sync)


if __name__ == "__main__":
    main()

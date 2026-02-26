#!/usr/bin/env python3
"""
Slack Notifier Example
======================
Send notifications and messages to Slack using Composio.

Prerequisites:
- Slack connected in Composio dashboard
- COMPOSIO_API_KEY set in environment

Usage:
    python slack-notifier.py send --channel general --message "Hello!"
    python slack-notifier.py list-channels
    python slack-notifier.py watch --channel general
"""

import os
import sys
import argparse
import time
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


class SlackNotifier:
    """Slack notification helper using Composio."""
    
    def __init__(self):
        """Initialize the notifier."""
        self.toolset = ComposioToolSet()
        self._verify_connection()
    
    def _verify_connection(self):
        """Verify Slack is connected."""
        try:
            connections = self.toolset.get_connected_accounts()
            slack_connected = any(
                c.app_name.lower() == "slack"
                for c in connections
            )
            
            if not slack_connected:
                print("⚠ Slack not connected")
                print("Connect at: https://app.composio.dev")
                sys.exit(1)
            
            print("✓ Slack connected")
        except Exception as e:
            print(f"⚠ Connection check failed: {e}")
    
    def list_channels(self, limit=100):
        """
        List available Slack channels.
        
        Args:
            limit: Maximum channels to fetch
        
        Returns:
            List of channels
        """
        try:
            result = self.toolset.execute_action(
                action=Action.SLACK_LIST_CHANNELS,
                params={"limit": limit}
            )
            
            if result.get("error"):
                print(f"Error: {result['error']}")
                return []
            
            return result.get("data", {}).get("channels", [])
        
        except Exception as e:
            print(f"Error listing channels: {e}")
            return []
    
    def send_message(self, channel, message, thread_ts=None):
        """
        Send a message to a channel.
        
        Args:
            channel: Channel name or ID
            message: Message text
            thread_ts: Optional thread timestamp for replies
        
        Returns:
            Message data or None
        """
        params = {
            "channel": channel,
            "text": message
        }
        
        if thread_ts:
            params["thread_ts"] = thread_ts
        
        try:
            result = self.toolset.execute_action(
                action=Action.SLACK_SEND_MESSAGE,
                params=params
            )
            
            if result.get("error"):
                print(f"Error: {result['error']}")
                return None
            
            return result.get("data", {})
        
        except Exception as e:
            print(f"Error sending message: {e}")
            return None
    
    def send_rich_message(self, channel, blocks, text=""):
        """
        Send a rich message with blocks.
        
        Args:
            channel: Channel name or ID
            blocks: Slack block kit blocks
            text: Fallback text
        
        Returns:
            Message data or None
        """
        try:
            result = self.toolset.execute_action(
                action=Action.SLACK_SEND_MESSAGE,
                params={
                    "channel": channel,
                    "text": text,
                    "blocks": blocks
                }
            )
            
            if result.get("error"):
                print(f"Error: {result['error']}")
                return None
            
            return result.get("data", {})
        
        except Exception as e:
            print(f"Error sending rich message: {e}")
            return None
    
    def get_messages(self, channel, limit=10):
        """
        Get recent messages from a channel.
        
        Args:
            channel: Channel name or ID
            limit: Maximum messages to fetch
        
        Returns:
            List of messages
        """
        try:
            result = self.toolset.execute_action(
                action=Action.SLACK_GET_CHANNEL_HISTORY,
                params={
                    "channel": channel,
                    "limit": limit
                }
            )
            
            if result.get("error"):
                print(f"Error: {result['error']}")
                return []
            
            return result.get("data", {}).get("messages", [])
        
        except Exception as e:
            print(f"Error getting messages: {e}")
            return []
    
    def add_reaction(self, channel, timestamp, emoji):
        """
        Add a reaction to a message.
        
        Args:
            channel: Channel ID
            timestamp: Message timestamp
            emoji: Emoji name (without colons)
        
        Returns:
            Success boolean
        """
        try:
            result = self.toolset.execute_action(
                action=Action.SLACK_ADD_REACTION,
                params={
                    "channel": channel,
                    "timestamp": timestamp,
                    "name": emoji
                }
            )
            
            return not result.get("error")
        
        except Exception as e:
            print(f"Error adding reaction: {e}")
            return False


def create_notification_blocks(title, message, level="info", fields=None):
    """
    Create Slack blocks for a notification.
    
    Args:
        title: Notification title
        message: Main message
        level: Severity level (info, warning, error, success)
        fields: Optional dict of field name -> value
    
    Returns:
        List of Slack blocks
    """
    # Color emoji by level
    level_emoji = {
        "info": "ℹ️",
        "warning": "⚠️",
        "error": "🚨",
        "success": "✅"
    }
    emoji = level_emoji.get(level, "📢")
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{emoji} {title}"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": message
            }
        }
    ]
    
    # Add fields if provided
    if fields:
        field_blocks = []
        for name, value in fields.items():
            field_blocks.append({
                "type": "mrkdwn",
                "text": f"*{name}:*\n{value}"
            })
        
        blocks.append({
            "type": "section",
            "fields": field_blocks[:10]  # Slack limit
        })
    
    # Add timestamp
    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            }
        ]
    })
    
    return blocks


def cmd_send(args, notifier):
    """Send message command."""
    print(f"\n📤 Sending to #{args.channel}")
    print("-" * 40)
    
    if args.rich:
        # Send rich notification
        blocks = create_notification_blocks(
            title=args.title or "Notification",
            message=args.message,
            level=args.level
        )
        result = notifier.send_rich_message(args.channel, blocks, args.message)
    else:
        # Send simple message
        result = notifier.send_message(args.channel, args.message)
    
    if result:
        print(f"✓ Message sent")
        print(f"  Timestamp: {result.get('ts')}")
    else:
        print("✗ Failed to send message")


def cmd_list_channels(args, notifier):
    """List channels command."""
    print("\n📋 Available Channels")
    print("=" * 40)
    
    channels = notifier.list_channels()
    
    if not channels:
        print("No channels found.")
        return
    
    for ch in channels:
        name = ch.get("name", "?")
        members = ch.get("num_members", 0)
        private = "🔒" if ch.get("is_private") else "📢"
        
        print(f"{private} #{name} ({members} members)")
    
    print(f"\nTotal: {len(channels)} channel(s)")


def cmd_notify(args, notifier):
    """Send rich notification command."""
    print(f"\n🔔 Sending notification to #{args.channel}")
    print("-" * 40)
    
    # Parse fields if provided
    fields = None
    if args.fields:
        fields = {}
        for field in args.fields:
            if "=" in field:
                name, value = field.split("=", 1)
                fields[name] = value
    
    blocks = create_notification_blocks(
        title=args.title,
        message=args.message,
        level=args.level,
        fields=fields
    )
    
    result = notifier.send_rich_message(
        args.channel,
        blocks,
        f"{args.title}: {args.message}"
    )
    
    if result:
        print(f"✓ Notification sent")
    else:
        print("✗ Failed to send notification")


def cmd_watch(args, notifier):
    """Watch channel command."""
    print(f"\n👀 Watching #{args.channel}")
    print("Press Ctrl+C to stop")
    print("-" * 40)
    
    seen_ts = set()
    
    try:
        while True:
            messages = notifier.get_messages(args.channel, 5)
            
            for msg in reversed(messages):
                ts = msg.get("ts")
                if ts and ts not in seen_ts:
                    seen_ts.add(ts)
                    user = msg.get("user", "unknown")
                    text = msg.get("text", "")[:100]
                    print(f"[@{user}] {text}")
            
            time.sleep(args.interval)
    
    except KeyboardInterrupt:
        print("\n\nStopped watching.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Slack Notifier")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Send command
    send_parser = subparsers.add_parser("send", help="Send message")
    send_parser.add_argument("--channel", "-c", required=True, help="Channel name")
    send_parser.add_argument("--message", "-m", required=True, help="Message text")
    send_parser.add_argument("--rich", action="store_true", help="Send as rich message")
    send_parser.add_argument("--title", help="Title for rich message")
    send_parser.add_argument("--level", default="info", 
                            choices=["info", "warning", "error", "success"])
    
    # List channels command
    list_parser = subparsers.add_parser("list-channels", help="List channels")
    
    # Notify command
    notify_parser = subparsers.add_parser("notify", help="Send notification")
    notify_parser.add_argument("--channel", "-c", required=True, help="Channel name")
    notify_parser.add_argument("--title", "-t", required=True, help="Notification title")
    notify_parser.add_argument("--message", "-m", required=True, help="Message text")
    notify_parser.add_argument("--level", "-l", default="info",
                              choices=["info", "warning", "error", "success"])
    notify_parser.add_argument("--fields", "-f", nargs="+", help="Fields as name=value")
    
    # Watch command
    watch_parser = subparsers.add_parser("watch", help="Watch channel")
    watch_parser.add_argument("--channel", "-c", required=True, help="Channel name")
    watch_parser.add_argument("--interval", "-i", type=int, default=5, help="Poll interval")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    print("=" * 40)
    print("💬 Slack Notifier")
    print("=" * 40)
    
    notifier = SlackNotifier()
    
    commands = {
        "send": cmd_send,
        "list-channels": cmd_list_channels,
        "notify": cmd_notify,
        "watch": cmd_watch
    }
    
    commands[args.command](args, notifier)


if __name__ == "__main__":
    main()

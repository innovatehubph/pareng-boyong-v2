#!/usr/bin/env python3
"""
Email Summarizer Example
========================
Summarizes unread Gmail emails using Composio + LLM.

Prerequisites:
- Gmail connected in Composio dashboard
- COMPOSIO_API_KEY set in environment
- OpenAI API key (optional, for better summaries)

Usage:
    python email-summarizer.py
    python email-summarizer.py --limit 5
    python email-summarizer.py --unread-only
"""

import os
import sys
import argparse
from datetime import datetime, timedelta

# Add parent directory to path for imports
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


def get_gmail_emails(toolset, limit=10, unread_only=True):
    """
    Fetch emails from Gmail using Composio.
    
    Args:
        toolset: ComposioToolSet instance
        limit: Maximum number of emails to fetch
        unread_only: Only fetch unread emails
    
    Returns:
        List of email dictionaries
    """
    try:
        # Build query
        query = "is:unread" if unread_only else ""
        
        # Execute Gmail list action
        result = toolset.execute_action(
            action=Action.GMAIL_LIST_EMAILS,
            params={
                "max_results": limit,
                "query": query
            }
        )
        
        if result.get("error"):
            print(f"Error fetching emails: {result['error']}")
            return []
        
        return result.get("data", {}).get("messages", [])
    
    except Exception as e:
        print(f"Error: {e}")
        return []


def get_email_content(toolset, message_id):
    """
    Get full content of a single email.
    
    Args:
        toolset: ComposioToolSet instance
        message_id: Gmail message ID
    
    Returns:
        Email content dictionary
    """
    try:
        result = toolset.execute_action(
            action=Action.GMAIL_GET_EMAIL,
            params={"message_id": message_id}
        )
        
        if result.get("error"):
            return None
        
        return result.get("data", {})
    
    except Exception as e:
        print(f"Error getting email: {e}")
        return None


def summarize_email(email_content):
    """
    Generate a simple summary of an email.
    For better results, integrate with an LLM.
    
    Args:
        email_content: Email content dictionary
    
    Returns:
        Summary string
    """
    subject = email_content.get("subject", "No Subject")
    sender = email_content.get("from", "Unknown")
    snippet = email_content.get("snippet", "")
    
    # Extract date
    date_str = email_content.get("date", "")
    
    # Simple extraction of key info
    summary = f"""
📧 **{subject}**
   From: {sender}
   Date: {date_str}
   Preview: {snippet[:150]}{'...' if len(snippet) > 150 else ''}
"""
    return summary.strip()


def summarize_with_llm(emails, openai_key=None):
    """
    Use an LLM to create a comprehensive summary.
    
    Args:
        emails: List of email content
        openai_key: Optional OpenAI API key
    
    Returns:
        LLM-generated summary
    """
    if not openai_key:
        openai_key = os.environ.get("OPENAI_API_KEY")
    
    if not openai_key:
        return None
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=openai_key)
        
        # Format emails for prompt
        email_text = "\n\n---\n\n".join([
            f"Subject: {e.get('subject', 'N/A')}\n"
            f"From: {e.get('from', 'N/A')}\n"
            f"Body: {e.get('snippet', 'N/A')}"
            for e in emails
        ])
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are an email assistant. Summarize the following emails concisely, highlighting key action items and important information."
                },
                {
                    "role": "user",
                    "content": f"Please summarize these emails:\n\n{email_text}"
                }
            ],
            max_tokens=500
        )
        
        return response.choices[0].message.content
    
    except ImportError:
        print("Note: Install openai package for LLM summaries")
        return None
    except Exception as e:
        print(f"LLM summary error: {e}")
        return None


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Summarize Gmail emails")
    parser.add_argument("--limit", type=int, default=10, help="Number of emails to fetch")
    parser.add_argument("--unread-only", action="store_true", default=True, help="Only unread emails")
    parser.add_argument("--all", action="store_true", help="Include read emails")
    parser.add_argument("--use-llm", action="store_true", help="Use LLM for summary")
    args = parser.parse_args()
    
    if args.all:
        args.unread_only = False
    
    print("=" * 60)
    print("📬 Email Summarizer")
    print("=" * 60)
    print()
    
    # Initialize Composio
    try:
        toolset = ComposioToolSet()
        print("✓ Connected to Composio")
    except Exception as e:
        print(f"✗ Failed to connect: {e}")
        print("\nMake sure COMPOSIO_API_KEY is set and Gmail is connected.")
        sys.exit(1)
    
    # Check if Gmail is connected
    try:
        connections = toolset.get_connected_accounts()
        gmail_connected = any(
            c.app_name.lower() == "gmail" 
            for c in connections
        )
        
        if not gmail_connected:
            print("✗ Gmail not connected")
            print("\nConnect Gmail at: https://app.composio.dev")
            sys.exit(1)
        
        print("✓ Gmail is connected")
    except Exception as e:
        print(f"⚠ Could not verify Gmail connection: {e}")
    
    print()
    print(f"Fetching {'unread ' if args.unread_only else ''}emails (limit: {args.limit})...")
    print()
    
    # Fetch emails
    messages = get_gmail_emails(toolset, args.limit, args.unread_only)
    
    if not messages:
        print("No emails found.")
        return
    
    print(f"Found {len(messages)} email(s)")
    print("-" * 60)
    print()
    
    # Get full content and summarize each
    email_contents = []
    for msg in messages:
        content = get_email_content(toolset, msg.get("id"))
        if content:
            email_contents.append(content)
            summary = summarize_email(content)
            print(summary)
            print()
    
    # Optional LLM summary
    if args.use_llm and email_contents:
        print("=" * 60)
        print("🤖 AI Summary")
        print("=" * 60)
        
        llm_summary = summarize_with_llm(email_contents)
        if llm_summary:
            print(llm_summary)
        else:
            print("LLM summary not available. Set OPENAI_API_KEY for this feature.")
    
    print()
    print("=" * 60)
    print(f"Total: {len(email_contents)} email(s) summarized")
    print("=" * 60)


if __name__ == "__main__":
    main()

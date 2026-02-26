#!/usr/bin/env python3
"""
GitHub Issue Tracker Example
=============================
Track and manage GitHub issues using Composio.

Prerequisites:
- GitHub connected in Composio dashboard
- COMPOSIO_API_KEY set in environment

Usage:
    python github-issue-tracker.py list --repo owner/repo
    python github-issue-tracker.py create --repo owner/repo --title "Bug fix"
    python github-issue-tracker.py summary --repo owner/repo
"""

import os
import sys
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


class GitHubTracker:
    """GitHub issue tracking using Composio."""
    
    def __init__(self):
        """Initialize the tracker."""
        self.toolset = ComposioToolSet()
        self._verify_connection()
    
    def _verify_connection(self):
        """Verify GitHub is connected."""
        try:
            connections = self.toolset.get_connected_accounts()
            github_connected = any(
                c.app_name.lower() == "github"
                for c in connections
            )
            
            if not github_connected:
                print("⚠ GitHub not connected")
                print("Connect at: https://app.composio.dev")
                sys.exit(1)
            
            print("✓ GitHub connected")
        except Exception as e:
            print(f"⚠ Connection check failed: {e}")
    
    def list_issues(self, repo, state="open", limit=20):
        """
        List issues for a repository.
        
        Args:
            repo: Repository in format 'owner/repo'
            state: Issue state ('open', 'closed', 'all')
            limit: Maximum issues to fetch
        
        Returns:
            List of issues
        """
        owner, repo_name = repo.split("/")
        
        try:
            result = self.toolset.execute_action(
                action=Action.GITHUB_LIST_ISSUES,
                params={
                    "owner": owner,
                    "repo": repo_name,
                    "state": state,
                    "per_page": limit
                }
            )
            
            if result.get("error"):
                print(f"Error: {result['error']}")
                return []
            
            return result.get("data", [])
        
        except Exception as e:
            print(f"Error listing issues: {e}")
            return []
    
    def create_issue(self, repo, title, body="", labels=None):
        """
        Create a new issue.
        
        Args:
            repo: Repository in format 'owner/repo'
            title: Issue title
            body: Issue body/description
            labels: List of label names
        
        Returns:
            Created issue data or None
        """
        owner, repo_name = repo.split("/")
        
        params = {
            "owner": owner,
            "repo": repo_name,
            "title": title,
            "body": body
        }
        
        if labels:
            params["labels"] = labels
        
        try:
            result = self.toolset.execute_action(
                action=Action.GITHUB_CREATE_ISSUE,
                params=params
            )
            
            if result.get("error"):
                print(f"Error: {result['error']}")
                return None
            
            return result.get("data", {})
        
        except Exception as e:
            print(f"Error creating issue: {e}")
            return None
    
    def get_issue(self, repo, issue_number):
        """
        Get details of a specific issue.
        
        Args:
            repo: Repository in format 'owner/repo'
            issue_number: Issue number
        
        Returns:
            Issue data or None
        """
        owner, repo_name = repo.split("/")
        
        try:
            result = self.toolset.execute_action(
                action=Action.GITHUB_GET_ISSUE,
                params={
                    "owner": owner,
                    "repo": repo_name,
                    "issue_number": issue_number
                }
            )
            
            if result.get("error"):
                return None
            
            return result.get("data", {})
        
        except Exception as e:
            print(f"Error getting issue: {e}")
            return None
    
    def add_comment(self, repo, issue_number, comment):
        """
        Add a comment to an issue.
        
        Args:
            repo: Repository in format 'owner/repo'
            issue_number: Issue number
            comment: Comment text
        
        Returns:
            Comment data or None
        """
        owner, repo_name = repo.split("/")
        
        try:
            result = self.toolset.execute_action(
                action=Action.GITHUB_CREATE_ISSUE_COMMENT,
                params={
                    "owner": owner,
                    "repo": repo_name,
                    "issue_number": issue_number,
                    "body": comment
                }
            )
            
            if result.get("error"):
                print(f"Error: {result['error']}")
                return None
            
            return result.get("data", {})
        
        except Exception as e:
            print(f"Error adding comment: {e}")
            return None
    
    def close_issue(self, repo, issue_number):
        """
        Close an issue.
        
        Args:
            repo: Repository in format 'owner/repo'
            issue_number: Issue number
        
        Returns:
            Updated issue data or None
        """
        owner, repo_name = repo.split("/")
        
        try:
            result = self.toolset.execute_action(
                action=Action.GITHUB_UPDATE_ISSUE,
                params={
                    "owner": owner,
                    "repo": repo_name,
                    "issue_number": issue_number,
                    "state": "closed"
                }
            )
            
            if result.get("error"):
                print(f"Error: {result['error']}")
                return None
            
            return result.get("data", {})
        
        except Exception as e:
            print(f"Error closing issue: {e}")
            return None


def format_issue(issue):
    """Format an issue for display."""
    number = issue.get("number", "?")
    title = issue.get("title", "No title")
    state = issue.get("state", "unknown")
    user = issue.get("user", {}).get("login", "unknown")
    created = issue.get("created_at", "")[:10]
    labels = [l.get("name", "") for l in issue.get("labels", [])]
    comments = issue.get("comments", 0)
    
    state_icon = "🟢" if state == "open" else "🔴"
    label_str = f" [{', '.join(labels)}]" if labels else ""
    
    return f"{state_icon} #{number}: {title}{label_str}\n   By @{user} on {created} | {comments} comments"


def cmd_list(args, tracker):
    """List issues command."""
    print(f"\n📋 Issues for {args.repo}")
    print("=" * 60)
    
    issues = tracker.list_issues(args.repo, args.state, args.limit)
    
    if not issues:
        print("No issues found.")
        return
    
    for issue in issues:
        print(format_issue(issue))
        print()
    
    print(f"Total: {len(issues)} issue(s)")


def cmd_create(args, tracker):
    """Create issue command."""
    print(f"\n➕ Creating issue in {args.repo}")
    print("-" * 60)
    
    labels = args.labels.split(",") if args.labels else None
    
    issue = tracker.create_issue(
        args.repo,
        args.title,
        args.body or "",
        labels
    )
    
    if issue:
        print(f"✓ Created issue #{issue.get('number')}")
        print(f"  URL: {issue.get('html_url')}")
    else:
        print("✗ Failed to create issue")


def cmd_view(args, tracker):
    """View issue command."""
    issue = tracker.get_issue(args.repo, args.number)
    
    if not issue:
        print(f"Issue #{args.number} not found")
        return
    
    print(f"\n📝 Issue #{issue.get('number')}: {issue.get('title')}")
    print("=" * 60)
    print(f"State: {issue.get('state')}")
    print(f"Author: @{issue.get('user', {}).get('login')}")
    print(f"Created: {issue.get('created_at')}")
    print(f"Updated: {issue.get('updated_at')}")
    print(f"Comments: {issue.get('comments')}")
    
    labels = [l.get("name") for l in issue.get("labels", [])]
    if labels:
        print(f"Labels: {', '.join(labels)}")
    
    print("-" * 60)
    print(issue.get("body", "No description"))
    print("-" * 60)
    print(f"URL: {issue.get('html_url')}")


def cmd_comment(args, tracker):
    """Add comment command."""
    result = tracker.add_comment(args.repo, args.number, args.comment)
    
    if result:
        print(f"✓ Added comment to issue #{args.number}")
    else:
        print("✗ Failed to add comment")


def cmd_close(args, tracker):
    """Close issue command."""
    result = tracker.close_issue(args.repo, args.number)
    
    if result:
        print(f"✓ Closed issue #{args.number}")
    else:
        print("✗ Failed to close issue")


def cmd_summary(args, tracker):
    """Summary command."""
    print(f"\n📊 Issue Summary for {args.repo}")
    print("=" * 60)
    
    open_issues = tracker.list_issues(args.repo, "open", 100)
    closed_issues = tracker.list_issues(args.repo, "closed", 100)
    
    print(f"Open issues: {len(open_issues)}")
    print(f"Closed issues: {len(closed_issues)}")
    
    if open_issues:
        # Group by labels
        label_counts = {}
        for issue in open_issues:
            for label in issue.get("labels", []):
                name = label.get("name", "unlabeled")
                label_counts[name] = label_counts.get(name, 0) + 1
        
        if label_counts:
            print("\nOpen issues by label:")
            for label, count in sorted(label_counts.items(), key=lambda x: -x[1]):
                print(f"  • {label}: {count}")
        
        # Recent issues
        print("\nRecent open issues:")
        for issue in open_issues[:5]:
            print(f"  #{issue.get('number')}: {issue.get('title')[:50]}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="GitHub Issue Tracker")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List issues")
    list_parser.add_argument("--repo", required=True, help="Repository (owner/repo)")
    list_parser.add_argument("--state", default="open", choices=["open", "closed", "all"])
    list_parser.add_argument("--limit", type=int, default=20)
    
    # Create command
    create_parser = subparsers.add_parser("create", help="Create issue")
    create_parser.add_argument("--repo", required=True, help="Repository (owner/repo)")
    create_parser.add_argument("--title", required=True, help="Issue title")
    create_parser.add_argument("--body", help="Issue body")
    create_parser.add_argument("--labels", help="Comma-separated labels")
    
    # View command
    view_parser = subparsers.add_parser("view", help="View issue")
    view_parser.add_argument("--repo", required=True, help="Repository (owner/repo)")
    view_parser.add_argument("--number", type=int, required=True, help="Issue number")
    
    # Comment command
    comment_parser = subparsers.add_parser("comment", help="Add comment")
    comment_parser.add_argument("--repo", required=True, help="Repository (owner/repo)")
    comment_parser.add_argument("--number", type=int, required=True, help="Issue number")
    comment_parser.add_argument("--comment", required=True, help="Comment text")
    
    # Close command
    close_parser = subparsers.add_parser("close", help="Close issue")
    close_parser.add_argument("--repo", required=True, help="Repository (owner/repo)")
    close_parser.add_argument("--number", type=int, required=True, help="Issue number")
    
    # Summary command
    summary_parser = subparsers.add_parser("summary", help="Issue summary")
    summary_parser.add_argument("--repo", required=True, help="Repository (owner/repo)")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    print("=" * 60)
    print("🐙 GitHub Issue Tracker")
    print("=" * 60)
    
    tracker = GitHubTracker()
    
    commands = {
        "list": cmd_list,
        "create": cmd_create,
        "view": cmd_view,
        "comment": cmd_comment,
        "close": cmd_close,
        "summary": cmd_summary
    }
    
    commands[args.command](args, tracker)


if __name__ == "__main__":
    main()

"""
Token Priority Fix - Ensures environment variables ALWAYS take priority
Import this at the top of innovatehub_claude.py to override token retrieval
"""
import os

def get_prioritized_api_key():
    """
    Get API key with strict priority:
    1. API_KEY_INNOVATEHUB env var
    2. API_KEY_ANTHROPIC env var  
    3. Never fall back to oauth file (causes stale token issues)
    """
    token = os.environ.get('API_KEY_INNOVATEHUB', '').strip()
    if token and token != 'None':
        return token
    
    token = os.environ.get('API_KEY_ANTHROPIC', '').strip()
    if token and token != 'None':
        return token
    
    return None

# Monkey-patch on import
import sys
if 'python.helpers.innovatehub_claude' in sys.modules:
    mod = sys.modules['python.helpers.innovatehub_claude']
    mod.get_innovatehub_api_key = lambda: get_prioritized_api_key()
    mod.get_valid_innovatehub_api_key = lambda: get_prioritized_api_key()

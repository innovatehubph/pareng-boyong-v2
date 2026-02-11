"""
Token Usage Manager for Pareng Boyong
Tracks and limits token consumption to prevent exhausting Claude Max quota
Similar to Claude Code's usage management
"""

import time
import json
import os
from typing import Optional, Dict, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
import asyncio

# Token usage tracking file
USAGE_TRACKING_FILE = "tmp/token_usage.json"
USAGE_LIMIT_CONFIG_FILE = "tmp/token_limits.json"


@dataclass
class TokenUsage:
    """Tracks token usage for a period"""
    timestamp: float
    period: str  # "daily", "hourly", "per_conversation"
    model_type: str  # "chat", "utility", "embedding"
    model_name: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    request_count: int = 0
    cost_usd: float = 0.0
    throttled: bool = False
    blocked: bool = False

    def __post_init__(self):
        self.total_tokens = self.input_tokens + self.output_tokens


@dataclass
class UsageLimitConfig:
    """Configuration for token usage limits"""
    daily_limit: int = 1_000_000  # 1M tokens/day for Claude Max
    hourly_limit: int = 100_000   # 100K tokens/hour (burst protection)
    per_conversation_limit: int = 50_000  # 50K tokens per single conversation

    # Throttling thresholds (% of limit)
    throttle_at_percent: float = 0.7  # Start throttling at 70%
    block_at_percent: float = 0.95    # Block at 95%
    warn_at_percent: float = 0.60     # Warn at 60%

    # Feature costs (pre-calculated token costs for various operations)
    memory_recall_query_cost: int = 750  # tokens for memory query generation
    memory_filter_cost: int = 1500       # tokens for post-filter validation
    memory_consolidation_cost: int = 2000  # tokens per memory fragment analysis
    chat_rename_cost: int = 800          # tokens for chat renaming
    keyword_extract_cost: int = 350      # tokens per keyword extraction

    # Optimization flags
    skip_memory_query_gen: bool = False     # If query unchanged, skip generation
    skip_memory_post_filter: bool = False   # Skip memory validation step
    batch_memory_consolidation: bool = False  # Batch multiple memories in one call
    compress_history: bool = False          # Compress old conversation history
    reduce_context_window: bool = False     # Use smaller context %

    # Scheduling
    enable_rate_limiting: bool = True
    enable_adaptive_throttling: bool = True
    enable_predictive_throttling: bool = False


class TokenUsageManager:
    """
    Manages token usage tracking, limiting, and optimization
    Prevents exceeding Claude Max quota
    """

    def __init__(self):
        self.config = UsageLimitConfig()
        self.usage_history: list[TokenUsage] = []
        self.daily_usage = 0
        self.hourly_usage = 0
        self.conversation_usage = 0
        self.conversation_start_time = 0
        self.last_warning_time = 0
        self.blocked_until_time = 0
        self.daily_reset_time = self._get_daily_reset_time()
        self.hourly_reset_time = time.time() + 3600
        self._load_config()
        self._load_usage_history()

    def _get_daily_reset_time(self) -> float:
        """Get next daily reset time (midnight UTC)"""
        tomorrow = datetime.utcnow() + timedelta(days=1)
        reset = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
        return reset.timestamp()

    def _load_config(self) -> None:
        """Load usage limit configuration"""
        config_path = self._get_path(USAGE_LIMIT_CONFIG_FILE)
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    data = json.load(f)
                    for key, value in data.items():
                        if hasattr(self.config, key):
                            setattr(self.config, key, value)
            except Exception:
                pass

    def _save_config(self) -> None:
        """Save usage limit configuration"""
        config_path = self._get_path(USAGE_LIMIT_CONFIG_FILE)
        try:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(asdict(self.config), f, indent=2)
        except Exception:
            pass

    def _load_usage_history(self) -> None:
        """Load usage history from file"""
        usage_path = self._get_path(USAGE_TRACKING_FILE)
        if os.path.exists(usage_path):
            try:
                with open(usage_path, 'r') as f:
                    data = json.load(f)
                    self.daily_usage = data.get('daily_usage', 0)
                    self.hourly_usage = data.get('hourly_usage', 0)
                    self.daily_reset_time = data.get('daily_reset_time', self._get_daily_reset_time())
                    self.hourly_reset_time = data.get('hourly_reset_time', time.time() + 3600)
            except Exception:
                pass

    def _save_usage_history(self) -> None:
        """Save usage history to file"""
        usage_path = self._get_path(USAGE_TRACKING_FILE)
        try:
            os.makedirs(os.path.dirname(usage_path), exist_ok=True)
            with open(usage_path, 'w') as f:
                json.dump({
                    'daily_usage': self.daily_usage,
                    'hourly_usage': self.hourly_usage,
                    'daily_reset_time': self.daily_reset_time,
                    'hourly_reset_time': self.hourly_reset_time,
                    'last_update': time.time()
                }, f, indent=2)
        except Exception:
            pass

    def _get_path(self, relative_path: str) -> str:
        """Get absolute path for relative path"""
        from python.helpers import files
        return files.get_abs_path(relative_path)

    def _check_reset_periods(self) -> None:
        """Check if periods have reset"""
        now = time.time()

        # Check daily reset
        if now >= self.daily_reset_time:
            self.daily_usage = 0
            self.daily_reset_time = self._get_daily_reset_time()

        # Check hourly reset
        if now >= self.hourly_reset_time:
            self.hourly_usage = 0
            self.hourly_reset_time = now + 3600

    def track_usage(
        self,
        model_type: str,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        request_count: int = 1
    ) -> Dict[str, Any]:
        """
        Track API usage and return throttling status
        Returns: {
            'allowed': bool,
            'throttled': bool,
            'blocked': bool,
            'reason': str,
            'daily_usage': int,
            'hourly_usage': int,
            'conversation_usage': int,
            'warning': Optional[str]
        }
        """
        self._check_reset_periods()

        total_tokens = input_tokens + output_tokens

        # Update usage counters
        self.daily_usage += total_tokens
        self.hourly_usage += total_tokens
        self.conversation_usage += total_tokens

        # Create usage record
        usage = TokenUsage(
            timestamp=time.time(),
            period="mixed",
            model_type=model_type,
            model_name=model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            request_count=request_count
        )
        self.usage_history.append(usage)

        # Keep only last 1000 records
        if len(self.usage_history) > 1000:
            self.usage_history = self.usage_history[-1000:]

        self._save_usage_history()

        # Check limits and return status
        return self._check_usage_limits()

    def _check_usage_limits(self) -> Dict[str, Any]:
        """Check if usage has exceeded limits"""
        now = time.time()
        status = {
            'allowed': True,
            'throttled': False,
            'blocked': False,
            'reason': None,
            'daily_usage': self.daily_usage,
            'hourly_usage': self.hourly_usage,
            'conversation_usage': self.conversation_usage,
            'warning': None
        }

        # Check if temporarily blocked
        if now < self.blocked_until_time:
            status['allowed'] = False
            status['blocked'] = True
            status['reason'] = f"Blocked until {datetime.fromtimestamp(self.blocked_until_time)}"
            return status

        # Check daily limit
        daily_percent = (self.daily_usage / self.config.daily_limit) * 100
        if self.daily_usage >= self.config.daily_limit * (self.config.block_at_percent / 100):
            status['allowed'] = False
            status['blocked'] = True
            status['reason'] = f"Daily limit blocked: {daily_percent:.1f}% used"
            self.blocked_until_time = now + 3600  # Block for 1 hour
            return status

        # Check hourly limit
        hourly_percent = (self.hourly_usage / self.config.hourly_limit) * 100
        if self.hourly_usage >= self.config.hourly_limit * (self.config.block_at_percent / 100):
            status['allowed'] = False
            status['blocked'] = True
            status['reason'] = f"Hourly limit blocked: {hourly_percent:.1f}% used"
            self.blocked_until_time = now + 600  # Block for 10 minutes
            return status

        # Check conversation limit
        conv_percent = (self.conversation_usage / self.config.per_conversation_limit) * 100
        if self.conversation_usage >= self.config.per_conversation_limit:
            status['warning'] = f"Conversation usage limit reached: {conv_percent:.1f}% used"

        # Check throttling thresholds
        if daily_percent >= self.config.throttle_at_percent * 100:
            status['throttled'] = True
            status['reason'] = f"Daily limit throttling: {daily_percent:.1f}% used"

        if hourly_percent >= self.config.throttle_at_percent * 100:
            status['throttled'] = True
            status['reason'] = f"Hourly limit throttling: {hourly_percent:.1f}% used"

        # Warning threshold
        if daily_percent >= self.config.warn_at_percent * 100:
            if now - self.last_warning_time > 3600:  # Warn once per hour
                status['warning'] = f"Daily usage high: {daily_percent:.1f}% of limit ({self.daily_usage:,} tokens used)"
                self.last_warning_time = now

        return status

    def should_skip_feature(self, feature: str) -> bool:
        """
        Determine if a feature should be skipped based on usage and configuration
        Features: 'memory_recall', 'memory_consolidation', 'chat_rename', etc.
        """
        usage_percent = min(
            (self.daily_usage / self.config.daily_limit) * 100,
            (self.hourly_usage / self.config.hourly_limit) * 100
        )

        # At 80%+ usage, skip expensive features
        if usage_percent > 80:
            return feature in ['memory_consolidation', 'memory_filter', 'chat_rename', 'keyword_extract']

        # At 90%+ usage, skip all optional features
        if usage_percent > 90:
            return feature in ['memory_recall', 'memory_consolidation', 'memory_filter', 'chat_rename', 'keyword_extract']

        return False

    def estimate_feature_cost(self, feature: str, iterations: int = 1) -> int:
        """Estimate token cost for a feature"""
        costs = {
            'memory_recall_query': self.config.memory_recall_query_cost,
            'memory_filter': self.config.memory_filter_cost,
            'memory_consolidation': self.config.memory_consolidation_cost * iterations,
            'chat_rename': self.config.chat_rename_cost,
            'keyword_extract': self.config.keyword_extract_cost * iterations,
        }
        return costs.get(feature, 0)

    def get_remaining_budget(self) -> Dict[str, int]:
        """Get remaining token budget"""
        return {
            'daily_remaining': max(0, self.config.daily_limit - self.daily_usage),
            'hourly_remaining': max(0, self.config.hourly_limit - self.hourly_usage),
            'conversation_remaining': max(0, self.config.per_conversation_limit - self.conversation_usage)
        }

    def get_usage_status(self) -> Dict[str, Any]:
        """Get current usage status"""
        remaining = self.get_remaining_budget()
        daily_percent = (self.daily_usage / self.config.daily_limit) * 100
        hourly_percent = (self.hourly_usage / self.config.hourly_limit) * 100
        conv_percent = (self.conversation_usage / self.config.per_conversation_limit) * 100

        return {
            'daily_usage': self.daily_usage,
            'daily_limit': self.config.daily_limit,
            'daily_percent': daily_percent,
            'daily_remaining': remaining['daily_remaining'],
            'hourly_usage': self.hourly_usage,
            'hourly_limit': self.config.hourly_limit,
            'hourly_percent': hourly_percent,
            'hourly_remaining': remaining['hourly_remaining'],
            'conversation_usage': self.conversation_usage,
            'conversation_limit': self.config.per_conversation_limit,
            'conversation_percent': conv_percent,
            'conversation_remaining': remaining['conversation_remaining'],
            'status': self._get_status_summary(daily_percent, hourly_percent),
            'blocked': time.time() < self.blocked_until_time,
            'throttled': daily_percent > self.config.throttle_at_percent * 100
        }

    def _get_status_summary(self, daily_pct: float, hourly_pct: float) -> str:
        """Get human-readable status"""
        if time.time() < self.blocked_until_time:
            return "🔴 Blocked"
        if max(daily_pct, hourly_pct) > 95:
            return "🔴 Critical"
        if max(daily_pct, hourly_pct) > 80:
            return "🟠 High"
        if max(daily_pct, hourly_pct) > 60:
            return "🟡 Medium"
        return "🟢 Low"

    def reset_conversation(self) -> None:
        """Reset conversation token usage"""
        self.conversation_usage = 0
        self.conversation_start_time = time.time()

    def set_limit(self, limit_type: str, value: int) -> None:
        """Update usage limits"""
        if limit_type == "daily":
            self.config.daily_limit = value
        elif limit_type == "hourly":
            self.config.hourly_limit = value
        elif limit_type == "conversation":
            self.config.per_conversation_limit = value
        self._save_config()

    def enable_optimization_mode(self, mode: str = "conservative") -> None:
        """Enable optimization mode: aggressive, conservative, balanced"""
        if mode == "aggressive":
            self.config.skip_memory_query_gen = True
            self.config.skip_memory_post_filter = True
            self.config.batch_memory_consolidation = True
            self.config.compress_history = True
            self.config.reduce_context_window = True
        elif mode == "conservative":
            self.config.skip_memory_post_filter = True
            self.config.compress_history = False
            self.config.batch_memory_consolidation = False
        elif mode == "balanced":
            self.config.skip_memory_post_filter = False
            self.config.batch_memory_consolidation = True
            self.config.compress_history = False

        self._save_config()


# Global instance
_instance: Optional[TokenUsageManager] = None


def get_instance() -> TokenUsageManager:
    """Get or create global token usage manager instance"""
    global _instance
    if _instance is None:
        _instance = TokenUsageManager()
    return _instance

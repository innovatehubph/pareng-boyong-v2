"""
Token Usage Optimizer for Pareng Boyong
Implements smart optimizations based on current usage patterns
Similar to Claude Code's usage optimization strategies
"""

from typing import Optional, Dict, Any
from .token_usage_manager import TokenUsageManager, get_instance as get_usage_manager


class TokenOptimizer:
    """
    Optimizes token usage based on usage patterns and limits
    Provides recommendations for feature disable/enable
    """

    def __init__(self):
        self.usage_manager = get_usage_manager()

    def should_enable_memory_recall(self) -> bool:
        """Determine if memory recall should be enabled"""
        return not self.usage_manager.should_skip_feature('memory_recall')

    def should_enable_memory_consolidation(self) -> bool:
        """Determine if memory consolidation should be enabled"""
        return not self.usage_manager.should_skip_feature('memory_consolidation')

    def should_enable_memory_filter(self) -> bool:
        """Determine if memory post-filter should be enabled"""
        return not self.usage_manager.should_skip_feature('memory_filter')

    def should_skip_chat_rename(self) -> bool:
        """Determine if chat renaming should be skipped"""
        return self.usage_manager.should_skip_feature('chat_rename')

    def get_recommended_memory_recall_interval(self) -> int:
        """Get recommended memory recall interval based on usage"""
        usage_percent = min(
            (self.usage_manager.daily_usage / self.usage_manager.config.daily_limit) * 100,
            (self.usage_manager.hourly_usage / self.usage_manager.config.hourly_limit) * 100
        )

        # Adaptive interval based on usage
        if usage_percent > 85:
            return 10  # Recall less frequently
        elif usage_percent > 70:
            return 7
        elif usage_percent > 50:
            return 5
        else:
            return 3  # Default

    def get_context_window_reduction(self) -> float:
        """Get recommended context window reduction factor"""
        usage_percent = min(
            (self.usage_manager.daily_usage / self.usage_manager.config.daily_limit) * 100,
            (self.usage_manager.hourly_usage / self.usage_manager.config.hourly_limit) * 100
        )

        # Reduce context window usage when approaching limits
        if usage_percent > 85:
            return 0.3  # Use only 30% of context
        elif usage_percent > 70:
            return 0.45
        elif usage_percent > 50:
            return 0.55
        else:
            return 0.7  # Default

    def should_batch_memories(self) -> bool:
        """Should memory consolidation be batched"""
        usage_percent = min(
            (self.usage_manager.daily_usage / self.usage_manager.config.daily_limit) * 100,
            (self.usage_manager.hourly_usage / self.usage_manager.config.hourly_limit) * 100
        )
        return usage_percent > 60

    def should_compress_history(self) -> bool:
        """Should chat history be compressed"""
        usage_percent = min(
            (self.usage_manager.daily_usage / self.usage_manager.config.daily_limit) * 100,
            (self.usage_manager.hourly_usage / self.usage_manager.config.hourly_limit) * 100
        )
        return usage_percent > 70

    def get_optimization_suggestions(self) -> Dict[str, str]:
        """Get human-readable optimization suggestions"""
        status = self.usage_manager.get_usage_status()
        suggestions = {}

        daily_pct = status['daily_percent']
        hourly_pct = status['hourly_percent']

        if daily_pct > 85 or hourly_pct > 85:
            suggestions['urgent'] = (
                f"⚠️ URGENT: Using {max(daily_pct, hourly_pct):.1f}% of limit. "
                "Memory features disabled. Consider reducing activity."
            )

        if daily_pct > 70:
            suggestions['daily'] = (
                f"🟠 Daily usage high: {daily_pct:.1f}%. "
                "Memory consolidation disabled to preserve tokens."
            )

        if hourly_pct > 70:
            suggestions['hourly'] = (
                f"🟠 Hourly usage high: {hourly_pct:.1f}%. "
                "Memory recalls less frequent."
            )

        if status['conversation_percent'] > 80:
            suggestions['conversation'] = (
                f"Conversation usage at {status['conversation_percent']:.1f}%. "
                "Consider starting a new conversation."
            )

        return suggestions

    def get_settings_recommendations(self) -> Dict[str, Any]:
        """Get recommended settings for token optimization"""
        usage_percent = min(
            (self.usage_manager.daily_usage / self.usage_manager.config.daily_limit) * 100,
            (self.usage_manager.hourly_usage / self.usage_manager.config.hourly_limit) * 100
        )

        recommendations = {
            'memory_recall_enabled': usage_percent < 85,
            'memory_recall_interval': self.get_recommended_memory_recall_interval(),
            'memory_recall_post_filter': usage_percent < 70,
            'memory_memorize_consolidation': usage_percent < 70,
            'chat_model_ctx_history': self.get_context_window_reduction(),
            'skip_chat_rename': usage_percent > 70,
            'batch_memory_consolidation': usage_percent > 60,
        }

        return recommendations

    def apply_auto_optimization(self) -> Dict[str, Any]:
        """Automatically apply optimization based on current usage"""
        recommendations = self.get_settings_recommendations()

        # Update usage manager config
        if not recommendations['memory_recall_enabled']:
            self.usage_manager.config.skip_memory_query_gen = True
            self.usage_manager.config.skip_memory_post_filter = True

        if recommendations['batch_memory_consolidation']:
            self.usage_manager.config.batch_memory_consolidation = True

        if recommendations['skip_chat_rename']:
            # Note: This would need to be handled by caller since settings are separate
            pass

        self.usage_manager._save_config()

        return {
            'applied': True,
            'changes': recommendations,
            'status': self.usage_manager.get_usage_status()
        }


class TokenUsageTracker:
    """
    Tracks token usage across conversations
    Records usage statistics for analysis
    """

    def __init__(self):
        self.usage_manager = get_usage_manager()

    def track_api_call(
        self,
        model_type: str,
        model_name: str,
        input_tokens: int,
        output_tokens: int
    ) -> Dict[str, Any]:
        """
        Track an API call and return usage status
        Returns status and recommendations
        """
        status = self.usage_manager.track_usage(
            model_type=model_type,
            model_name=model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens
        )

        # Get current usage
        usage_status = self.usage_manager.get_usage_status()

        return {
            'tracked': True,
            'total_tokens': input_tokens + output_tokens,
            'usage_status': usage_status,
            'limit_status': status,
            'throttled': status['throttled'],
            'blocked': status['blocked'],
            'warning': status.get('warning')
        }

    def start_conversation(self) -> None:
        """Mark start of new conversation"""
        self.usage_manager.reset_conversation()

    def end_conversation(self) -> Dict[str, Any]:
        """Mark end of conversation and return stats"""
        usage = self.usage_manager.conversation_usage
        limit = self.usage_manager.config.per_conversation_limit
        percent = (usage / limit * 100) if limit > 0 else 0

        return {
            'conversation_tokens': usage,
            'conversation_limit': limit,
            'conversation_percent': percent,
            'remained_in_limit': usage <= limit
        }

    def get_daily_summary(self) -> Dict[str, Any]:
        """Get daily usage summary"""
        status = self.usage_manager.get_usage_status()

        return {
            'period': 'daily',
            'used': status['daily_usage'],
            'limit': status['daily_limit'],
            'percent': status['daily_percent'],
            'remaining': status['daily_remaining'],
            'status': status['status'],
            'blocked': status['blocked'],
            'throttled': status['throttled']
        }

    def get_hourly_summary(self) -> Dict[str, Any]:
        """Get hourly usage summary"""
        status = self.usage_manager.get_usage_status()

        return {
            'period': 'hourly',
            'used': status['hourly_usage'],
            'limit': status['hourly_limit'],
            'percent': status['hourly_percent'],
            'remaining': status['hourly_remaining'],
            'status': status['status'],
            'blocked': status['blocked']
        }

    def export_stats(self) -> Dict[str, Any]:
        """Export all statistics for monitoring"""
        usage = self.usage_manager
        status = usage.get_usage_status()

        return {
            'timestamp': __import__('time').time(),
            'daily': {
                'used': usage.daily_usage,
                'limit': usage.config.daily_limit,
                'percent': status['daily_percent'],
                'remaining': status['daily_remaining']
            },
            'hourly': {
                'used': usage.hourly_usage,
                'limit': usage.config.hourly_limit,
                'percent': status['hourly_percent'],
                'remaining': status['hourly_remaining']
            },
            'conversation': {
                'used': usage.conversation_usage,
                'limit': usage.config.per_conversation_limit,
                'percent': status['conversation_percent'],
                'remaining': status['conversation_remaining']
            },
            'status': {
                'overall': status['status'],
                'blocked': status['blocked'],
                'throttled': status['throttled']
            },
            'history_size': len(usage.usage_history)
        }


# Global instances
_optimizer_instance: Optional[TokenOptimizer] = None
_tracker_instance: Optional[TokenUsageTracker] = None


def get_optimizer() -> TokenOptimizer:
    """Get global token optimizer instance"""
    global _optimizer_instance
    if _optimizer_instance is None:
        _optimizer_instance = TokenOptimizer()
    return _optimizer_instance


def get_tracker() -> TokenUsageTracker:
    """Get global token usage tracker instance"""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = TokenUsageTracker()
    return _tracker_instance

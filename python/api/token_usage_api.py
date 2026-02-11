"""
Token Usage API Handler
Provides endpoints for monitoring and managing token usage
"""

from python.helpers.api import ApiHandler, Request, Response
from python.helpers.token_usage_manager import get_instance as get_usage_manager
from python.helpers.token_optimizer import get_optimizer, get_tracker


class TokenUsageAPI(ApiHandler):
    """
    Token usage management API

    Endpoints:
    - GET: Get current usage status
    - POST action=status: Get detailed status
    - POST action=summary: Get daily/hourly summary
    - POST action=recommendations: Get optimization recommendations
    - POST action=optimize: Auto-apply optimizations
    - POST action=set_limit: Update usage limits
    - POST action=stats: Export all statistics
    """

    async def process(self, input: dict, request: Request) -> dict | Response:
        action = input.get("action", "status")

        if request.method == "GET" or action == "status":
            return await self.get_status()
        elif action == "summary":
            return await self.get_summary()
        elif action == "recommendations":
            return await self.get_recommendations()
        elif action == "optimize":
            return await self.auto_optimize()
        elif action == "set_limit":
            return await self.set_limit(input)
        elif action == "stats":
            return await self.export_stats()
        else:
            return {"error": f"Unknown action: {action}"}

    async def get_status(self) -> dict:
        """Get current token usage status"""
        manager = get_usage_manager()
        status = manager.get_usage_status()

        return {
            "status": "success",
            "data": {
                "daily": {
                    "used": status['daily_usage'],
                    "limit": status['daily_limit'],
                    "percent": round(status['daily_percent'], 1),
                    "remaining": status['daily_remaining'],
                    "indicator": self._get_indicator(status['daily_percent'])
                },
                "hourly": {
                    "used": status['hourly_usage'],
                    "limit": status['hourly_limit'],
                    "percent": round(status['hourly_percent'], 1),
                    "remaining": status['hourly_remaining'],
                    "indicator": self._get_indicator(status['hourly_percent'])
                },
                "conversation": {
                    "used": status['conversation_usage'],
                    "limit": status['conversation_limit'],
                    "percent": round(status['conversation_percent'], 1),
                    "remaining": status['conversation_remaining'],
                    "indicator": self._get_indicator(status['conversation_percent'])
                },
                "overall_status": status['status'],
                "blocked": status['blocked'],
                "throttled": status['throttled']
            }
        }

    async def get_summary(self) -> dict:
        """Get usage summary"""
        tracker = get_tracker()

        return {
            "status": "success",
            "daily": tracker.get_daily_summary(),
            "hourly": tracker.get_hourly_summary(),
            "conversation": tracker.end_conversation()
        }

    async def get_recommendations(self) -> dict:
        """Get optimization recommendations"""
        optimizer = get_optimizer()
        suggestions = optimizer.get_optimization_suggestions()
        recommendations = optimizer.get_settings_recommendations()

        return {
            "status": "success",
            "suggestions": suggestions,
            "recommendations": recommendations,
            "priority": self._get_suggestion_priority(suggestions)
        }

    async def auto_optimize(self) -> dict:
        """Apply automatic optimizations"""
        optimizer = get_optimizer()
        result = optimizer.apply_auto_optimization()

        return {
            "status": "success",
            "message": "Optimizations applied based on current usage",
            "applied_changes": result['changes'],
            "current_status": result['status']
        }

    async def set_limit(self, input: dict) -> dict:
        """Update usage limits"""
        limit_type = input.get("limit_type")  # "daily", "hourly", "conversation"
        value = input.get("value")

        if not limit_type or value is None:
            return {"error": "Missing limit_type or value"}

        if not isinstance(value, int) or value <= 0:
            return {"error": "Value must be positive integer"}

        manager = get_usage_manager()
        manager.set_limit(limit_type, value)

        return {
            "status": "success",
            "message": f"Updated {limit_type} limit to {value:,} tokens",
            "new_config": {
                "daily_limit": manager.config.daily_limit,
                "hourly_limit": manager.config.hourly_limit,
                "conversation_limit": manager.config.per_conversation_limit
            }
        }

    async def export_stats(self) -> dict:
        """Export all statistics"""
        tracker = get_tracker()
        stats = tracker.export_stats()

        return {
            "status": "success",
            "statistics": stats,
            "timestamp": stats['timestamp']
        }

    def _get_indicator(self, percent: float) -> str:
        """Get visual indicator for usage percent"""
        if percent >= 95:
            return "🔴"  # Critical
        elif percent >= 80:
            return "🟠"  # High
        elif percent >= 60:
            return "🟡"  # Medium
        else:
            return "🟢"  # Low

    def _get_suggestion_priority(self, suggestions: dict) -> str:
        """Get priority level from suggestions"""
        if 'urgent' in suggestions:
            return "🔴 URGENT"
        elif 'daily' in suggestions or 'hourly' in suggestions:
            return "🟠 HIGH"
        elif 'conversation' in suggestions:
            return "🟡 MEDIUM"
        else:
            return "🟢 LOW"

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST"]

    @classmethod
    def requires_auth(cls) -> bool:
        return True


class TokenOptimizationConfigAPI(ApiHandler):
    """
    Configure token optimization settings

    Endpoints:
    - GET: Get current optimization config
    - POST mode: Apply optimization mode (aggressive, balanced, conservative)
    """

    async def process(self, input: dict, request: Request) -> dict | Response:
        mode = input.get("mode")

        if request.method == "GET":
            return await self.get_config()
        elif mode:
            return await self.set_optimization_mode(mode)
        else:
            return {"error": "Missing mode parameter"}

    async def get_config(self) -> dict:
        """Get current optimization configuration"""
        manager = get_usage_manager()
        config = manager.config

        return {
            "status": "success",
            "limits": {
                "daily": config.daily_limit,
                "hourly": config.hourly_limit,
                "per_conversation": config.per_conversation_limit
            },
            "thresholds": {
                "warn_at_percent": config.warn_at_percent * 100,
                "throttle_at_percent": config.throttle_at_percent * 100,
                "block_at_percent": config.block_at_percent * 100
            },
            "optimization": {
                "skip_memory_query_gen": config.skip_memory_query_gen,
                "skip_memory_post_filter": config.skip_memory_post_filter,
                "batch_memory_consolidation": config.batch_memory_consolidation,
                "compress_history": config.compress_history,
                "reduce_context_window": config.reduce_context_window,
                "enable_rate_limiting": config.enable_rate_limiting,
                "enable_adaptive_throttling": config.enable_adaptive_throttling,
                "enable_predictive_throttling": config.enable_predictive_throttling
            },
            "feature_costs": {
                "memory_recall_query": config.memory_recall_query_cost,
                "memory_filter": config.memory_filter_cost,
                "memory_consolidation": config.memory_consolidation_cost,
                "chat_rename": config.chat_rename_cost,
                "keyword_extract": config.keyword_extract_cost
            }
        }

    async def set_optimization_mode(self, mode: str) -> dict:
        """Apply optimization mode"""
        if mode not in ["aggressive", "balanced", "conservative"]:
            return {"error": f"Unknown mode: {mode}. Use: aggressive, balanced, conservative"}

        manager = get_usage_manager()
        manager.enable_optimization_mode(mode)

        return {
            "status": "success",
            "message": f"Switched to {mode} optimization mode",
            "mode": mode,
            "config": await self.get_config()
        }

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST"]

    @classmethod
    def requires_auth(cls) -> bool:
        return True

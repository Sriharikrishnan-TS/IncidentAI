"""
Git History Agent Module

This agent analyzes git repository history to identify:
- High-churn services (services with frequent code changes)
- Recent commit activity
- Top contributors to the repository
"""

from .node import git_history_agent_node

__all__ = ["git_history_agent_node"]

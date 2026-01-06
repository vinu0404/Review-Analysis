"""
Prompts package initialization
"""

from app.prompts.user_prompts import USER_RESPONSE_PROMPT
from app.prompts.admin_prompts import ADMIN_SUMMARY_PROMPT, RECOMMENDED_ACTIONS_PROMPT

__all__ = ["USER_RESPONSE_PROMPT", "ADMIN_SUMMARY_PROMPT", "RECOMMENDED_ACTIONS_PROMPT"]

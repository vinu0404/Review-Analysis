"""
LLM Service for generating AI responses using structured output.
Single LLM call generates all three outputs: admin_summary, recommended_actions, user_response
"""

import logging
from typing import Dict, Any

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from app.config import get_settings
from app.prompts.unified_prompt import UNIFIED_REVIEW_ANALYSIS_PROMPT
from app.models import LLMReviewAnalysis

logger = logging.getLogger(__name__)

FALLBACK_RESPONSES = {
    5: "Thank you for your excellent review! We're thrilled that you had such a wonderful experience with us. Your kind words mean a lot to our team!",
    4: "Thank you for your positive feedback! We're glad you enjoyed your experience. We're always working to make things even better!",
    3: "Thank you for your honest review. We appreciate your feedback and are always looking for ways to improve your experience.",
    2: "We're sorry your experience didn't meet your expectations. Thank you for letting us know - your feedback helps us improve.",
    1: "We sincerely apologize for your disappointing experience. We take your feedback very seriously and will work hard to address these issues."
}


class LLMService:
    """Service for handling all LLM interactions using structured output"""
    
    def __init__(self):
        self.settings = get_settings()
        self._llm = None
        self._initialized = False
    
    def _get_llm(self, temperature: float = 0.5) -> ChatOpenAI:
        """Get LLM instance with specified temperature"""
        return ChatOpenAI(
            model=self.settings.llm_model,
            temperature=temperature,
            api_key=self.settings.openai_api_key,
            request_timeout=self.settings.llm_timeout
        )
    
    async def process_review(self, rating: int, review_text: str) -> Dict[str, Any]:
        """
        Process a review and generate all AI responses
        
        Args:
            rating: Star rating (1-5)
            review_text: The review text
            
        Returns:
            Dictionary with user_response, admin_summary, recommended_actions, model_used
        """
        try:
            llm = self._get_llm(temperature=0.5)
            structured_llm = llm.with_structured_output(LLMReviewAnalysis)
            prompt = ChatPromptTemplate.from_template(UNIFIED_REVIEW_ANALYSIS_PROMPT)
            chain = prompt | structured_llm
            result: LLMReviewAnalysis = await chain.ainvoke({
                "rating": rating,
                "review_text": review_text
            })
            
            logger.info(f"Successfully generated structured output for {rating}-star review")
            
            return {
                "user_response": result.user_response.strip(),
                "admin_summary": result.admin_summary.strip(),
                "recommended_actions": result.recommended_actions.strip(),
                "model_used": self.settings.llm_model
            }
            
        except Exception as e:
            logger.error(f"LLM structured output error: {e}")
            return {
                "user_response": self.get_fallback_response(rating),
                "admin_summary": f"[Processing failed] Rating: {rating}/5. Review length: {len(review_text)} chars.",
                "recommended_actions": self._get_fallback_actions(rating),
                "model_used": "fallback"
            }
    
    def get_fallback_response(self, rating: int) -> str:
        """Get fallback response when LLM fails"""
        return FALLBACK_RESPONSES.get(rating, FALLBACK_RESPONSES[3])
    
    def _get_fallback_actions(self, rating: int) -> str:
        """Get fallback recommended actions"""
        if rating >= 4:
            return "• Maintain current service standards\n• Consider featuring positive feedback\n• Thank the customer"
        elif rating == 3:
            return "• Review feedback for improvement areas\n• Follow up if specific issues mentioned\n• Monitor for patterns"
        else:
            return "• Prioritize addressing customer concerns\n• Consider direct outreach to customer\n• Review processes for improvement"

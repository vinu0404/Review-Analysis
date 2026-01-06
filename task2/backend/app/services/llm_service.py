"""
LLM Service for generating AI responses
"""

import asyncio
import logging
from typing import Dict, Any

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.config import get_settings
from app.prompts.user_prompts import USER_RESPONSE_PROMPT
from app.prompts.admin_prompts import ADMIN_SUMMARY_PROMPT, RECOMMENDED_ACTIONS_PROMPT

logger = logging.getLogger(__name__)

FALLBACK_RESPONSES = {
    5: "Thank you for your excellent review! We're thrilled that you had such a wonderful experience with us. Your kind words mean a lot to our team!",
    4: "Thank you for your positive feedback! We're glad you enjoyed your experience. We're always working to make things even better!",
    3: "Thank you for your honest review. We appreciate your feedback and are always looking for ways to improve your experience.",
    2: "We're sorry your experience didn't meet your expectations. Thank you for letting us know - your feedback helps us improve.",
    1: "We sincerely apologize for your disappointing experience. We take your feedback very seriously and will work hard to address these issues."
}


class LLMService:
    """Service for handling all LLM interactions"""
    
    def __init__(self):
        self.settings = get_settings()
        self._llm = None
        self._initialized = False
    
    def _get_llm(self, temperature: float = 0.7) -> ChatOpenAI:
        """Get LLM instance with specified temperature"""
        return ChatOpenAI(
            model=self.settings.llm_model,
            temperature=temperature,
            api_key=self.settings.openai_api_key,
            request_timeout=self.settings.llm_timeout
        )
    
    async def process_review(self, rating: int, review_text: str) -> Dict[str, Any]:
        """
        Process a review and generate all AI responses.
        
        Args:
            rating: Star rating (1-5)
            review_text: The review text
            
        Returns:
            Dictionary with user_response, admin_summary, recommended_actions, model_used
        """
        try:
            user_response_task = self._generate_user_response(rating, review_text)
            admin_summary_task = self._generate_admin_summary(rating, review_text)
            user_response, admin_summary = await asyncio.gather(
                user_response_task,
                admin_summary_task,
                return_exceptions=True
            )
            if isinstance(user_response, Exception):
                logger.error(f"User response generation failed: {user_response}")
                user_response = self.get_fallback_response(rating)
            
            if isinstance(admin_summary, Exception):
                logger.error(f"Admin summary generation failed: {admin_summary}")
                admin_summary = f"[Auto-summary failed] Rating: {rating}/5. Review length: {len(review_text)} chars."
            try:
                recommended_actions = await self._generate_recommended_actions(
                    rating, review_text, admin_summary
                )
            except Exception as e:
                logger.error(f"Recommended actions generation failed: {e}")
                recommended_actions = self._get_fallback_actions(rating)
            
            return {
                "user_response": user_response,
                "admin_summary": admin_summary,
                "recommended_actions": recommended_actions,
                "model_used": self.settings.llm_model
            }
            
        except Exception as e:
            logger.error(f"LLM processing error: {e}")
            return {
                "user_response": self.get_fallback_response(rating),
                "admin_summary": f"[Processing failed] Rating: {rating}/5",
                "recommended_actions": self._get_fallback_actions(rating),
                "model_used": "fallback"
            }
    
    async def _generate_user_response(self, rating: int, review_text: str) -> str:
        """Generate AI response for the user"""
        llm = self._get_llm(temperature=0.7)
        prompt = ChatPromptTemplate.from_template(USER_RESPONSE_PROMPT)
        chain = prompt | llm | StrOutputParser()
        
        response = await chain.ainvoke({
            "rating": rating,
            "review_text": review_text
        })
        
        return response.strip()
    
    async def _generate_admin_summary(self, rating: int, review_text: str) -> str:
        """Generate summary for admin dashboard"""
        llm = self._get_llm(temperature=0.3)
        prompt = ChatPromptTemplate.from_template(ADMIN_SUMMARY_PROMPT)
        chain = prompt | llm | StrOutputParser()
        
        response = await chain.ainvoke({
            "rating": rating,
            "review_text": review_text
        })
        
        return response.strip()
    
    async def _generate_recommended_actions(
        self, 
        rating: int, 
        review_text: str, 
        admin_summary: str
    ) -> str:
        """Generate recommended actions for admin"""
        llm = self._get_llm(temperature=0.5)
        prompt = ChatPromptTemplate.from_template(RECOMMENDED_ACTIONS_PROMPT)
        chain = prompt | llm | StrOutputParser()
        
        response = await chain.ainvoke({
            "rating": rating,
            "review_text": review_text,
            "admin_summary": admin_summary
        })
        
        return response.strip()
    
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

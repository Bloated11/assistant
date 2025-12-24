import asyncio
import logging
from typing import Optional, Dict, Any
from functools import partial

logger = logging.getLogger(__name__)

class AIService:
    """Service for handling AI interactions with proper async discipline"""
    
    def __init__(self, phenom):
        self.phenom = phenom
    
    async def generate_response(
        self,
        message: str,
        use_cloud: bool = False,
        provider: Optional[str] = None,
        system: Optional[str] = None
    ) -> str:
        """
        Generate AI response with proper async handling
        Offloads blocking AI calls to thread pool
        """
        try:
            loop = asyncio.get_event_loop()
            
            if use_cloud and provider:
                response = await loop.run_in_executor(
                    None,
                    partial(
                        self._generate_with_provider,
                        message=message,
                        provider=provider,
                        system=system
                    )
                )
            else:
                response = await loop.run_in_executor(
                    None,
                    partial(
                        self.phenom.ai.generate,
                        prompt=message,
                        system=system,
                        force_cloud=use_cloud
                    )
                )
            
            return response or "I'm having trouble processing that request right now."
            
        except Exception as e:
            logger.error(f"AI generation error: {e}")
            return "I encountered an error processing your message."
    
    def _generate_with_provider(
        self,
        message: str,
        provider: str,
        system: Optional[str] = None
    ) -> str:
        """
        Generate response with specific cloud provider
        This runs in a thread pool executor
        """
        original_provider = self.phenom.ai.cloud_llm.provider
        
        try:
            self.phenom.ai.cloud_llm.provider = provider
            self.phenom.ai.cloud_llm._initialize_client()
            
            response = self.phenom.ai.cloud_llm.generate(message, system)
            return response
            
        finally:
            self.phenom.ai.cloud_llm.provider = original_provider
            self.phenom.ai.cloud_llm._initialize_client()
    
    async def chat(
        self,
        messages: list,
        use_cloud: bool = False
    ) -> str:
        """
        Generate chat response with message history
        """
        try:
            loop = asyncio.get_event_loop()
            
            response = await loop.run_in_executor(
                None,
                partial(
                    self.phenom.ai.chat,
                    messages=messages,
                    force_cloud=use_cloud
                )
            )
            
            return response or "I'm having trouble processing that request right now."
            
        except Exception as e:
            logger.error(f"AI chat error: {e}")
            return "I encountered an error processing your message."
    
    def get_mode(self) -> str:
        """Get current AI mode (local/cloud/hybrid)"""
        return self.phenom.ai.mode
    
    def get_status(self) -> Dict[str, Any]:
        """Get AI system status"""
        return {
            "mode": self.phenom.ai.mode,
            "local_available": self.phenom.ai.local_llm.is_available() if self.phenom.ai.local_llm.enabled else False,
            "cloud_available": self.phenom.ai.cloud_llm.is_available() if self.phenom.ai.cloud_llm.enabled else False,
            "local_model": self.phenom.ai.local_llm.model if self.phenom.ai.local_llm.enabled else None,
            "cloud_provider": self.phenom.ai.cloud_llm.provider if self.phenom.ai.cloud_llm.enabled else None,
            "personal_injection": getattr(self.phenom.ai, 'personal_injection_enabled', False)
        }

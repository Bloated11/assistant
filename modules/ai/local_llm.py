import logging
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class LocalLLM:
    def __init__(self, config: dict):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.model = config.get('model', 'phi3:mini')
        self.base_url = config.get('base_url', 'http://localhost:11434')
        self.temperature = config.get('temperature', 0.7)
        self.num_ctx = config.get('num_ctx', 2048)
        self.num_thread = config.get('num_thread', 4)
        self.timeout = config.get('timeout', 60)
        self.max_tokens = config.get('max_tokens', None)
        
        logger.info(f"LocalLLM initialized with model {self.model} (threads: {self.num_thread}, ctx: {self.num_ctx})")
    
    def is_available(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def generate(self, prompt: str, system: str = None, context: list = None) -> Optional[str]:
        if not self.enabled:
            return None
        
        try:
            payload = {
                'model': self.model,
                'prompt': prompt,
                'stream': False,
                'options': {
                    'temperature': self.temperature,
                    'num_ctx': self.num_ctx,
                    'num_thread': self.num_thread
                }
            }
            
            if self.max_tokens:
                payload['options']['num_predict'] = self.max_tokens
            
            if system:
                payload['system'] = system
            
            if context:
                payload['context'] = context
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '')
            
            return None
            
        except Exception as e:
            logger.error(f"Local LLM generation error: {e}")
            return None
    
    def chat(self, messages: list) -> Optional[str]:
        if not self.enabled:
            return None
        
        try:
            payload = {
                'model': self.model,
                'messages': messages,
                'stream': False,
                'options': {
                    'temperature': self.temperature,
                    'num_ctx': self.num_ctx,
                    'num_thread': self.num_thread
                }
            }
            
            if self.max_tokens:
                payload['options']['num_predict'] = self.max_tokens
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('message', {}).get('content', '')
            
            return None
            
        except Exception as e:
            logger.error(f"Local LLM chat error: {e}")
            return None

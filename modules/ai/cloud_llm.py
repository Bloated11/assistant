import logging
from typing import Optional
import os

logger = logging.getLogger(__name__)

class CloudLLM:
    def __init__(self, config: dict):
        self.config = config
        self.enabled = config.get('enabled', False)
        self.provider = os.getenv('CLOUD_AI_PROVIDER', config.get('provider', 'openai'))
        
        # Set default model based on provider
        if self.provider == 'openai':
            default_model = 'gpt-3.5-turbo'
        elif self.provider == 'anthropic':
            default_model = 'claude-3-sonnet-20240229'
        elif self.provider == 'openrouter':
            default_model = 'anthropic/claude-3.5-sonnet'
        else:
            default_model = 'gpt-3.5-turbo'
        
        self.model = config.get('model', default_model)
        
        if self.provider == 'openai':
            self.api_key = os.getenv('OPENAI_API_KEY')
        elif self.provider == 'anthropic':
            self.api_key = os.getenv('ANTHROPIC_API_KEY')
        elif self.provider == 'openrouter':
            self.api_key = os.getenv('OPENROUTER_API_KEY')
            self.base_url = os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')
        else:
            self.api_key = None
        
        self.temperature = config.get('temperature', 0.7)
        self.max_tokens = config.get('max_tokens', 1024)
        
        self.client = None
        
        if self.enabled and self.api_key:
            self._initialize_client()
        
        logger.info(f"CloudLLM initialized with {self.provider}")
    
    def _initialize_client(self):
        try:
            if self.provider == 'openai':
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
            elif self.provider == 'anthropic':
                from anthropic import Anthropic
                self.client = Anthropic(api_key=self.api_key)
            elif self.provider == 'openrouter':
                from openai import OpenAI
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url
                )
        except Exception as e:
            logger.error(f"Error initializing cloud client: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        return self.enabled and self.client is not None
    
    def generate(self, prompt: str, system: str = None) -> Optional[str]:
        if not self.is_available():
            return None
        
        try:
            if self.provider in ['openai', 'openrouter']:
                return self._generate_openai(prompt, system)
            elif self.provider == 'anthropic':
                return self._generate_anthropic(prompt, system)
            
            return None
        except Exception as e:
            logger.error(f"Cloud LLM generation error: {e}")
            return None
    
    def _generate_openai(self, prompt: str, system: str = None) -> Optional[str]:
        messages = []
        
        if system:
            messages.append({"role": "system", "content": system})
        
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        
        return response.choices[0].message.content
    
    def _generate_anthropic(self, prompt: str, system: str = None) -> Optional[str]:
        kwargs = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        if system:
            kwargs["system"] = system
        
        response = self.client.messages.create(**kwargs)
        
        return response.content[0].text
    
    def chat(self, messages: list) -> Optional[str]:
        if not self.is_available():
            return None
        
        try:
            if self.provider in ['openai', 'openrouter']:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
                return response.choices[0].message.content
            
            elif self.provider == 'anthropic':
                system_msg = None
                user_messages = []
                
                for msg in messages:
                    if msg['role'] == 'system':
                        system_msg = msg['content']
                    else:
                        user_messages.append(msg)
                
                kwargs = {
                    "model": self.model,
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                    "messages": user_messages
                }
                
                if system_msg:
                    kwargs["system"] = system_msg
                
                response = self.client.messages.create(**kwargs)
                return response.content[0].text
            
            return None
        except Exception as e:
            logger.error(f"Cloud LLM chat error: {e}")
            return None

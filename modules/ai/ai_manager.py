import logging
from typing import Optional
import os
from .local_llm import LocalLLM
from .cloud_llm import CloudLLM

logger = logging.getLogger(__name__)

class AIManager:
    def __init__(self, config: dict):
        self.config = config
        self.mode = os.getenv('AI_MODE', config.get('mode', 'hybrid'))
        self.decision_threshold = config.get('decision_threshold', 0.5)
        
        # Personal injection config (opt-in)
        pi_conf = config.get('personal_injection', {})
        self.personal_injection_enabled = pi_conf.get('enabled', False)
        # If env_keys is empty, we fall back to collecting all env vars prefixed with 'PHENOM_'
        self.personal_env_keys = pi_conf.get('env_keys', [])
        # A short directive to prepend when injecting personal data
        self.personal_directive = pi_conf.get('directive', "Use the user's personal information to provide personalized replies when appropriate.")
        
        self.local_llm = LocalLLM(config.get('local', {}))
        self.cloud_llm = CloudLLM(config.get('cloud', {}))
        
        logger.info(f"AIManager initialized in {self.mode} mode (personal injection: {self.personal_injection_enabled})")
    
    def _build_system_prompt(self) -> Optional[str]:
        """Construct a short system prompt from selected env vars when enabled."""
        if not self.personal_injection_enabled:
            return None
        collected = {}

        # Use explicit keys if provided
        if self.personal_env_keys:
            for k in self.personal_env_keys:
                v = os.getenv(k)
                if v:
                    collected[k] = v
        else:
            # Fallback: collect env vars that start with PHENOM_
            for k, v in os.environ.items():
                if k.startswith('PHENOM_') and v:
                    collected[k] = v

        if not collected:
            return None

        lines = [self.personal_directive.strip(), ""]
        for k, v in collected.items():
            lines.append(f"{k}: {v}")
        # Keep it reasonably short
        prompt = "\n".join(lines)
        return prompt

    def generate(self, prompt: str, system: str = None, force_cloud: bool = False) -> str:
        # If caller did not provide a system prompt, try to build one from env/config
        if system is None:
            system = self._build_system_prompt()

        if self.mode == 'local':
            response = self.local_llm.generate(prompt, system)
            return response or "I'm having trouble processing that request."
        
        elif self.mode == 'cloud':
            response = self.cloud_llm.generate(prompt, system)
            return response or "I'm having trouble connecting to my cloud services."
        
        elif self.mode == 'hybrid':
            if force_cloud or self._should_use_cloud(prompt):
                if self.cloud_llm.is_available():
                    response = self.cloud_llm.generate(prompt, system)
                    if response:
                        return response
                
                if self.local_llm.is_available():
                    logger.info("Cloud failed, falling back to local LLM")
                    response = self.local_llm.generate(prompt, system)
                    if response:
                        return response
            else:
                if self.local_llm.is_available():
                    response = self.local_llm.generate(prompt, system)
                    if response:
                        return response
                
                if self.cloud_llm.is_available():
                    logger.info("Local LLM unavailable, using cloud")
                    response = self.cloud_llm.generate(prompt, system)
                    if response:
                        return response
        
        return "I'm currently unable to process your request."
    
    def chat(self, messages: list, force_cloud: bool = False) -> str:
        # If personal injection is enabled and messages don't include a system message,
        # prepend one constructed from env/config.
        system_prompt = None
        if self.personal_injection_enabled:
            # detect existing system message
            has_system = any(msg.get('role') == 'system' for msg in messages)
            if not has_system:
                system_prompt = self._build_system_prompt()
                if system_prompt:
                    # prepend a system message
                    messages = [{'role': 'system', 'content': system_prompt}] + messages

        if self.mode == 'local':
            response = self.local_llm.chat(messages)
            return response or "I'm having trouble processing that request."
        
        elif self.mode == 'cloud':
            response = self.cloud_llm.chat(messages)
            return response or "I'm having trouble connecting to my cloud services."
        
        elif self.mode == 'hybrid':
            last_message = messages[-1]['content'] if messages else ""
            
            if force_cloud or self._should_use_cloud(last_message):
                if self.cloud_llm.is_available():
                    response = self.cloud_llm.chat(messages)
                    if response:
                        return response
                
                if self.local_llm.is_available():
                    response = self.local_llm.chat(messages)
                    if response:
                        return response
            else:
                if self.local_llm.is_available():
                    response = self.local_llm.chat(messages)
                    if response:
                        return response
                
                if self.cloud_llm.is_available():
                    response = self.cloud_llm.chat(messages)
                    if response:
                        return response
        
        return "I'm currently unable to process your request."
    
    def _should_use_cloud(self, prompt: str) -> bool:
        # With higher threshold (0.8), we prefer local AI for most tasks
        # Only use cloud for very complex queries
        complex_keywords = [
            'analyze in detail', 'complex analysis', 'detailed explanation',
            'comprehensive', 'research paper', 'creative writing', 'translate entire'
        ]
        
        prompt_lower = prompt.lower()
        complexity_score = sum(1 for keyword in complex_keywords if keyword in prompt_lower)
        
        if len(prompt) > 500:  # Increased from 200
            complexity_score += 1
        
        normalized_score = min(complexity_score / 5.0, 1.0)
        
        return normalized_score >= self.decision_threshold
    
    def is_local_available(self) -> bool:
        return self.local_llm.is_available()
    
    def is_cloud_available(self) -> bool:
        return self.cloud_llm.is_available()
    
    def get_current_mode(self) -> str:
        return self.mode
    
    def generate_response(self, prompt: str, use_cloud: bool = False) -> str:
        return self.generate(prompt, force_cloud=use_cloud)

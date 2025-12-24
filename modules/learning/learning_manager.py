import logging
from typing import Dict, Any, List
from .memory import Memory

logger = logging.getLogger(__name__)

class LearningManager:
    def __init__(self, config: dict):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.learning_rate = config.get('learning_rate', 0.1)
        
        if self.enabled:
            self.memory = Memory(config)
        
        logger.info(f"LearningManager initialized (enabled: {self.enabled})")
    
    def process_interaction(self, user_input: str, response: str, metadata: Dict = None):
        if not self.enabled:
            return
        
        self.memory.add_conversation(user_input, response, metadata)
        
        self._extract_and_learn_patterns(user_input)
        
        self._update_preferences(user_input, metadata)
    
    def _extract_and_learn_patterns(self, text: str):
        words = text.lower().split()
        
        for i in range(len(words)):
            if i < len(words) - 1:
                bigram = f"{words[i]} {words[i+1]}"
                self.memory.learn_pattern(bigram)
            
            self.memory.learn_pattern(words[i])
    
    def _update_preferences(self, user_input: str, metadata: Dict = None):
        if not metadata:
            return
        
        if 'preferred_voice_rate' in metadata:
            current = self.memory.get_preference('voice_rate', 175)
            new_rate = metadata['preferred_voice_rate']
            updated = current * (1 - self.learning_rate) + new_rate * self.learning_rate
            self.memory.set_preference('voice_rate', int(updated))
    
    def get_contextual_response(self, query: str) -> str:
        similar_conversations = self.memory.search_conversations(query)
        
        if similar_conversations:
            most_recent = similar_conversations[-1]
            return f"Based on our previous conversation, {most_recent['assistant']}"
        
        return ""
    
    def get_user_profile(self) -> Dict[str, Any]:
        common_patterns = self.memory.get_common_patterns(10)
        
        return {
            'preferences': self.memory.user_preferences,
            'total_conversations': len(self.memory.conversations),
            'common_topics': [pattern[0] for pattern in common_patterns],
            'memory_items': len(self.memory.memory)
        }
    
    def remember_fact(self, key: str, value: Any):
        self.memory.remember(key, value)
    
    def recall_fact(self, key: str) -> Any:
        return self.memory.recall(key)
    
    def get_conversation_context(self, limit: int = 5) -> List[Dict]:
        return self.memory.get_recent_conversations(limit)

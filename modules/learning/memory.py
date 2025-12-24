import json
import logging
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)

class Memory:
    def __init__(self, config: dict):
        self.config = config
        self.memory_file = config.get('memory_file', 'data/memory.json')
        self.conversation_file = config.get('conversation_history', 'data/conversations.json')
        self.max_history = config.get('max_history', 1000)
        
        self.memory = {}
        self.conversations = []
        self.user_preferences = {}
        self.learned_patterns = defaultdict(int)
        
        self._load_memory()
        self._load_conversations()
        
        logger.info("Memory initialized")
    
    def _load_memory(self):
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r') as f:
                    content = f.read().strip()
                    if content:
                        data = json.loads(content)
                        self.memory = data.get('memory', {})
                        self.user_preferences = data.get('preferences', {})
                        self.learned_patterns = defaultdict(int, data.get('patterns', {}))
                        logger.info("Memory loaded from storage")
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in memory file: {e}. Starting with empty memory.")
        except Exception as e:
            logger.error(f"Error loading memory: {e}")
    
    def _save_memory(self):
        try:
            os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
            with open(self.memory_file, 'w') as f:
                json.dump({
                    'memory': self.memory,
                    'preferences': self.user_preferences,
                    'patterns': dict(self.learned_patterns),
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
            logger.debug("Memory saved")
        except Exception as e:
            logger.error(f"Error saving memory: {e}")
    
    def _load_conversations(self):
        try:
            if os.path.exists(self.conversation_file):
                with open(self.conversation_file, 'r') as f:
                    content = f.read().strip()
                    if content:
                        self.conversations = json.loads(content)
                        logger.info(f"Loaded {len(self.conversations)} conversations")
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in conversations file: {e}. Starting with empty history.")
        except Exception as e:
            logger.error(f"Error loading conversations: {e}")
    
    def _save_conversations(self):
        try:
            os.makedirs(os.path.dirname(self.conversation_file), exist_ok=True)
            
            if len(self.conversations) > self.max_history:
                self.conversations = self.conversations[-self.max_history:]
            
            with open(self.conversation_file, 'w') as f:
                json.dump(self.conversations, f, indent=2)
            logger.debug("Conversations saved")
        except Exception as e:
            logger.error(f"Error saving conversations: {e}")
    
    def remember(self, key: str, value: Any):
        self.memory[key] = {
            'value': value,
            'timestamp': datetime.now().isoformat()
        }
        self._save_memory()
        logger.info(f"Remembered: {key}")
    
    def recall(self, key: str) -> Optional[Any]:
        if key in self.memory:
            return self.memory[key]['value']
        return None
    
    def forget(self, key: str) -> bool:
        if key in self.memory:
            del self.memory[key]
            self._save_memory()
            logger.info(f"Forgot: {key}")
            return True
        return False
    
    def add_conversation(self, user_input: str, assistant_response: str, metadata: Dict = None):
        conversation = {
            'timestamp': datetime.now().isoformat(),
            'user': user_input,
            'assistant': assistant_response,
            'metadata': metadata or {}
        }
        
        self.conversations.append(conversation)
        self._save_conversations()
    
    def get_recent_conversations(self, limit: int = 10) -> List[Dict]:
        return self.conversations[-limit:]
    
    def search_conversations(self, query: str) -> List[Dict]:
        query_lower = query.lower()
        return [
            conv for conv in self.conversations
            if query_lower in conv['user'].lower() or 
               query_lower in conv['assistant'].lower()
        ]
    
    def set_preference(self, key: str, value: Any):
        self.user_preferences[key] = value
        self._save_memory()
        logger.info(f"Set preference: {key} = {value}")
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        return self.user_preferences.get(key, default)
    
    def learn_pattern(self, pattern: str):
        self.learned_patterns[pattern] += 1
        self._save_memory()
    
    def get_pattern_frequency(self, pattern: str) -> int:
        return self.learned_patterns.get(pattern, 0)
    
    def get_common_patterns(self, limit: int = 10) -> List[tuple]:
        sorted_patterns = sorted(
            self.learned_patterns.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_patterns[:limit]
    
    def get_context_summary(self, limit: int = 5) -> str:
        recent = self.get_recent_conversations(limit)
        
        if not recent:
            return "No recent conversation history."
        
        summary = "Recent conversation context:\n"
        for conv in recent:
            summary += f"User: {conv['user'][:100]}...\n"
            summary += f"Assistant: {conv['assistant'][:100]}...\n\n"
        
        return summary

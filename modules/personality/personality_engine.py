import logging
import random
from typing import List

logger = logging.getLogger(__name__)

class PersonalityEngine:
    def __init__(self, config: dict):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.mood = config.get('mood', 'helpful')
        self.humor = config.get('humor', True)
        self.formality = config.get('formality', 'balanced')
        self.verbosity = config.get('verbosity', 'normal')
        
        self.greetings = {
            'morning': ["Good morning!", "Rise and shine!", "Morning! Ready to start the day?"],
            'afternoon': ["Good afternoon!", "Hope you're having a great day!", "Afternoon!"],
            'evening': ["Good evening!", "Evening! How can I help?", "Good to see you!"],
            'night': ["Working late?", "Good night!", "Still here? Let me help."]
        }
        
        self.affirmations = [
            "Certainly!", "Of course!", "Absolutely!", "Right away!", "On it!",
            "Consider it done!", "I'm on it!", "Got it!", "You got it!"
        ]
        
        self.acknowledgments = [
            "Understood.", "Got it.", "Noted.", "I see.", "Clear.",
            "Acknowledged.", "Roger that.", "Affirmative."
        ]
        
        self.humor_responses = [
            "I'd make a joke about that, but my humor module is still loading... just kidding, it's ready!",
            "Processing... just kidding, I'm faster than that!",
            "My circuits are tingling with excitement about that request!",
            "Beep boop... sorry, wrong assistant. Let me help you properly!"
        ]
        
        logger.info(f"PersonalityEngine initialized (mood: {self.mood})")
    
    def enhance_response(self, response: str, context: str = None) -> str:
        if not self.enabled:
            return response
        
        enhanced = response
        
        if self.humor and random.random() < 0.1:
            enhanced = self._add_humor(enhanced)
        
        if self.formality == 'formal':
            enhanced = self._make_formal(enhanced)
        elif self.formality == 'casual':
            enhanced = self._make_casual(enhanced)
        
        return enhanced
    
    def _add_humor(self, text: str) -> str:
        if random.random() < 0.5 and len(text) > 50:
            humor = random.choice(self.humor_responses)
            return f"{text} {humor}"
        return text
    
    def _make_formal(self, text: str) -> str:
        replacements = {
            "ok": "very well",
            "yeah": "yes",
            "nope": "no",
            "sure": "certainly",
            "cool": "excellent"
        }
        
        result = text
        for informal, formal in replacements.items():
            result = result.replace(informal, formal)
        
        return result
    
    def _make_casual(self, text: str) -> str:
        replacements = {
            "Certainly": "Sure",
            "Indeed": "Yeah",
            "However": "But",
            "Therefore": "So"
        }
        
        result = text
        for formal, casual in replacements.items():
            result = result.replace(formal, casual)
        
        return result
    
    def get_greeting(self, time_of_day: str = 'morning') -> str:
        greetings = self.greetings.get(time_of_day, self.greetings['morning'])
        return random.choice(greetings)
    
    def get_affirmation(self) -> str:
        return random.choice(self.affirmations)
    
    def get_acknowledgment(self) -> str:
        return random.choice(self.acknowledgments)
    
    def express_empathy(self, situation: str) -> str:
        empathy_phrases = {
            'error': "I apologize for the inconvenience. Let me try to fix that.",
            'wait': "I understand waiting can be frustrating. I'm working as fast as I can.",
            'confusion': "I see you might be confused. Let me clarify that for you.",
            'success': "Excellent! I'm glad I could help.",
            'frustration': "I understand this is frustrating. Let's work through it together."
        }
        
        return empathy_phrases.get(situation, "I understand. How can I help?")
    
    def add_personality_markers(self, response: str) -> str:
        if not self.enabled:
            return response
        
        if self.mood == 'enthusiastic':
            if not response.endswith('!'):
                response += '!'
        elif self.mood == 'professional':
            response = response.rstrip('!')
        
        return response
    
    def contextualize_response(self, response: str, user_emotion: str = None) -> str:
        if user_emotion == 'frustrated':
            return self.express_empathy('frustration') + " " + response
        elif user_emotion == 'happy':
            return self.get_affirmation() + " " + response
        
        return response

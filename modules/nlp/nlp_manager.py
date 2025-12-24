import logging
import re
from typing import Dict, List, Tuple, Any
from collections import Counter

logger = logging.getLogger(__name__)

class NLPManager:
    def __init__(self, config: dict):
        self.enabled = config.get('enabled', True)
        
        self.intents = {
            'search': ['search', 'find', 'look up', 'google', 'what is', 'who is'],
            'task': ['task', 'todo', 'remind', 'reminder', 'add task', 'create task'],
            'system': ['system', 'status', 'info', 'performance', 'cpu', 'memory'],
            'execute': ['execute', 'run', 'command', 'launch', 'open'],
            'weather': ['weather', 'temperature', 'forecast'],
            'news': ['news', 'headlines', 'latest'],
            'calendar': ['calendar', 'schedule', 'event', 'meeting', 'appointment'],
            'email': ['email', 'mail', 'message', 'send'],
            'help': ['help', 'assist', 'how to', 'what can you do']
        }
        
        self.stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 
                          'to', 'for', 'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were'}
        
        if self.enabled:
            logger.info("NLP manager initialized")
    
    def classify_intent(self, text: str) -> Tuple[str, float]:
        if not self.enabled:
            return 'unknown', 0.0
        
        text_lower = text.lower()
        scores = {}
        
        for intent, keywords in self.intents.items():
            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1
                    if text_lower.startswith(keyword):
                        score += 1
            
            if score > 0:
                scores[intent] = score
        
        if scores:
            best_intent = max(scores, key=scores.get)
            max_score = scores[best_intent]
            confidence = min(max_score / 3.0, 1.0)
            return best_intent, confidence
        
        return 'general_query', 0.3
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        if not self.enabled:
            return {}
        
        entities = {
            'dates': [],
            'times': [],
            'numbers': [],
            'emails': [],
            'urls': [],
            'file_paths': []
        }
        
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',
            r'\d{2}/\d{2}/\d{4}',
            r'(today|tomorrow|yesterday)',
            r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
            r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}'
        ]
        
        time_patterns = [
            r'\d{1,2}:\d{2}\s*(am|pm)?',
            r'\d{1,2}\s*(am|pm)'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities['dates'].extend(matches)
        
        for pattern in time_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities['times'].extend([m if isinstance(m, str) else m[0] for m in matches])
        
        entities['numbers'] = re.findall(r'\b\d+\b', text)
        
        entities['emails'] = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        
        entities['urls'] = re.findall(r'https?://[^\s]+', text)
        
        entities['file_paths'] = re.findall(r'[/~][^\s]+', text)
        
        entities = {k: v for k, v in entities.items() if v}
        
        return entities
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        if not self.enabled:
            return {}
        
        positive_words = {'good', 'great', 'excellent', 'awesome', 'wonderful', 'fantastic',
                         'love', 'like', 'happy', 'pleased', 'thanks', 'thank you'}
        
        negative_words = {'bad', 'terrible', 'awful', 'horrible', 'hate', 'dislike',
                         'angry', 'sad', 'disappointed', 'frustrated', 'annoying'}
        
        words = text.lower().split()
        
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        total = positive_count + negative_count
        
        if total == 0:
            sentiment = 'neutral'
            score = 0.0
        elif positive_count > negative_count:
            sentiment = 'positive'
            score = positive_count / total
        else:
            sentiment = 'negative'
            score = negative_count / total
        
        return {
            'sentiment': sentiment,
            'score': score,
            'positive_words': positive_count,
            'negative_words': negative_count
        }
    
    def extract_keywords(self, text: str, num_keywords: int = 5) -> List[str]:
        if not self.enabled:
            return []
        
        words = re.findall(r'\b[a-z]+\b', text.lower())
        
        filtered_words = [w for w in words if w not in self.stop_words and len(w) > 3]
        
        word_freq = Counter(filtered_words)
        
        keywords = [word for word, count in word_freq.most_common(num_keywords)]
        
        return keywords
    
    def tokenize(self, text: str) -> List[str]:
        if not self.enabled:
            return []
        
        tokens = re.findall(r'\b\w+\b', text.lower())
        return tokens
    
    def remove_stop_words(self, text: str) -> str:
        if not self.enabled:
            return text
        
        words = text.split()
        filtered = [w for w in words if w.lower() not in self.stop_words]
        return ' '.join(filtered)
    
    def summarize_text(self, text: str, num_sentences: int = 3) -> str:
        if not self.enabled:
            return text
        
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) <= num_sentences:
            return text
        
        sentence_scores = {}
        for sentence in sentences:
            keywords = self.extract_keywords(sentence, 3)
            sentence_scores[sentence] = len(keywords)
        
        top_sentences = sorted(sentence_scores.items(), 
                              key=lambda x: x[1], 
                              reverse=True)[:num_sentences]
        
        summary_sentences = [s[0] for s in top_sentences]
        
        ordered_summary = []
        for sentence in sentences:
            if sentence in summary_sentences:
                ordered_summary.append(sentence)
        
        return '. '.join(ordered_summary) + '.'
    
    def detect_language(self, text: str) -> str:
        if not self.enabled:
            return 'en'
        
        english_indicators = {'the', 'is', 'are', 'and', 'for', 'to', 'of'}
        words = set(text.lower().split())
        
        if len(words & english_indicators) > 0:
            return 'en'
        
        return 'unknown'
    
    def get_statistics(self, text: str) -> Dict[str, Any]:
        if not self.enabled:
            return {}
        
        words = self.tokenize(text)
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return {
            'character_count': len(text),
            'word_count': len(words),
            'sentence_count': len(sentences),
            'average_word_length': sum(len(w) for w in words) / len(words) if words else 0,
            'average_sentence_length': len(words) / len(sentences) if sentences else 0,
            'unique_words': len(set(words))
        }

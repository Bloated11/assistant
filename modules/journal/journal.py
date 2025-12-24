import logging
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import uuid

logger = logging.getLogger(__name__)

class JournalSystem:
    def __init__(self, config: dict):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.storage_path = config.get('storage_path', 'data/journal.json')
        
        self.entries = {}
        self.prompts = {}
        self.tags = set()
        
        if self.enabled:
            self._load_data()
            self._load_default_prompts()
        
        logger.info("JournalSystem initialized")
    
    def _load_data(self):
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.entries = data.get('entries', {})
                    self.prompts = data.get('prompts', {})
                    self.tags = set(data.get('tags', []))
                logger.info(f"Loaded {len(self.entries)} journal entries")
        except Exception as e:
            logger.error(f"Error loading journal data: {e}")
    
    def _save_data(self):
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump({
                    'entries': self.entries,
                    'prompts': self.prompts,
                    'tags': list(self.tags),
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving journal data: {e}")
    
    def _load_default_prompts(self):
        if not self.prompts:
            self.prompts = {
                'gratitude': 'What are three things you are grateful for today?',
                'accomplishment': 'What did you accomplish today?',
                'challenge': 'What challenge did you face and how did you handle it?',
                'learning': 'What did you learn today?',
                'tomorrow': 'What are your goals for tomorrow?',
                'mood': 'How are you feeling today and why?',
                'reflection': 'What moment today made you pause and reflect?'
            }
    
    def create_entry(self, content: str, title: str = None, mood: str = None,
                    tags: List[str] = None, date: str = None) -> Optional[str]:
        if not self.enabled:
            return None
        
        try:
            entry_id = str(uuid.uuid4())[:8]
            entry_date = date or datetime.now().isoformat()
            
            entry_tags = tags or []
            self.tags.update(entry_tags)
            
            self.entries[entry_id] = {
                'id': entry_id,
                'title': title or f"Entry {datetime.now().strftime('%Y-%m-%d')}",
                'content': content,
                'mood': mood,
                'tags': entry_tags,
                'date': entry_date,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'favorite': False,
                'word_count': len(content.split())
            }
            
            self._save_data()
            logger.info(f"Created journal entry: {entry_id}")
            return entry_id
            
        except Exception as e:
            logger.error(f"Error creating journal entry: {e}")
            return None
    
    def update_entry(self, entry_id: str, content: str = None, title: str = None,
                    mood: str = None, tags: List[str] = None) -> bool:
        if not self.enabled or entry_id not in self.entries:
            return False
        
        try:
            if content:
                self.entries[entry_id]['content'] = content
                self.entries[entry_id]['word_count'] = len(content.split())
            
            if title:
                self.entries[entry_id]['title'] = title
            
            if mood:
                self.entries[entry_id]['mood'] = mood
            
            if tags:
                self.entries[entry_id]['tags'] = tags
                self.tags.update(tags)
            
            self.entries[entry_id]['updated_at'] = datetime.now().isoformat()
            
            self._save_data()
            logger.info(f"Updated journal entry: {entry_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating journal entry: {e}")
            return False
    
    def get_entry(self, entry_id: str) -> Optional[Dict[str, Any]]:
        if not self.enabled or entry_id not in self.entries:
            return None
        return self.entries[entry_id].copy()
    
    def get_todays_entry(self) -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None
        
        today = datetime.now().date().isoformat()
        for entry in self.entries.values():
            if entry['date'][:10] == today:
                return entry.copy()
        
        return None
    
    def search_entries(self, query: str = None, tag: str = None, mood: str = None,
                      start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        if not self.enabled:
            return []
        
        try:
            results = list(self.entries.values())
            
            if query:
                query_lower = query.lower()
                results = [e for e in results if query_lower in e['content'].lower() 
                          or query_lower in e['title'].lower()]
            
            if tag:
                results = [e for e in results if tag in e.get('tags', [])]
            
            if mood:
                results = [e for e in results if e.get('mood') == mood]
            
            if start_date:
                results = [e for e in results if e['date'] >= start_date]
            
            if end_date:
                results = [e for e in results if e['date'] <= end_date]
            
            return sorted(results, key=lambda x: x['date'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error searching entries: {e}")
            return []
    
    def toggle_favorite(self, entry_id: str) -> bool:
        if not self.enabled or entry_id not in self.entries:
            return False
        
        try:
            self.entries[entry_id]['favorite'] = not self.entries[entry_id]['favorite']
            self._save_data()
            return True
            
        except Exception as e:
            logger.error(f"Error toggling favorite: {e}")
            return False
    
    def delete_entry(self, entry_id: str) -> bool:
        if not self.enabled or entry_id not in self.entries:
            return False
        
        try:
            del self.entries[entry_id]
            self._save_data()
            logger.info(f"Deleted journal entry: {entry_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting entry: {e}")
            return False
    
    def get_prompt(self, prompt_type: str = None) -> str:
        if not self.enabled:
            return ""
        
        if prompt_type and prompt_type in self.prompts:
            return self.prompts[prompt_type]
        
        import random
        return random.choice(list(self.prompts.values()))
    
    def add_custom_prompt(self, name: str, prompt: str) -> bool:
        if not self.enabled:
            return False
        
        try:
            self.prompts[name] = prompt
            self._save_data()
            logger.info(f"Added custom prompt: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding custom prompt: {e}")
            return False
    
    def get_streak(self) -> int:
        if not self.enabled or not self.entries:
            return 0
        
        try:
            dates = sorted(set(e['date'][:10] for e in self.entries.values()), reverse=True)
            
            if not dates:
                return 0
            
            today = datetime.now().date()
            current_date = today
            streak = 0
            
            for date_str in dates:
                date = datetime.fromisoformat(date_str).date()
                
                if date == current_date:
                    streak += 1
                    current_date -= timedelta(days=1)
                elif date < current_date:
                    break
            
            return streak
            
        except Exception as e:
            logger.error(f"Error calculating streak: {e}")
            return 0
    
    def get_analytics(self, days: int = 30) -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None
        
        try:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            recent = [e for e in self.entries.values() if e['date'] >= cutoff]
            
            total_words = sum(e['word_count'] for e in recent)
            
            mood_counts = defaultdict(int)
            for e in recent:
                if e.get('mood'):
                    mood_counts[e['mood']] += 1
            
            tag_counts = defaultdict(int)
            for e in recent:
                for tag in e.get('tags', []):
                    tag_counts[tag] += 1
            
            daily_counts = defaultdict(int)
            for e in recent:
                date = e['date'][:10]
                daily_counts[date] += 1
            
            return {
                'period_days': days,
                'total_entries': len(recent),
                'total_words': total_words,
                'avg_words_per_entry': total_words / len(recent) if recent else 0,
                'current_streak': self.get_streak(),
                'mood_distribution': dict(mood_counts),
                'top_tags': dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
                'entries_per_day': len(recent) / days,
                'favorite_count': len([e for e in recent if e['favorite']])
            }
            
        except Exception as e:
            logger.error(f"Error getting analytics: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            'enabled': self.enabled,
            'total_entries': len(self.entries),
            'total_tags': len(self.tags),
            'current_streak': self.get_streak(),
            'favorite_count': len([e for e in self.entries.values() if e['favorite']])
        }

    def get_recent_entries(self, count: int = 10) -> List[Dict[str, Any]]:
        entries_list = []
        for entry_id, entry in self.entries.items():
            entry_copy = entry.copy()
            entry_copy['id'] = entry_id
            entries_list.append(entry_copy)
        return sorted(entries_list, key=lambda x: x.get('timestamp', ''), reverse=True)[:count]



    def add_entry(self, content: str, mood: str = None, title: str = None, **kwargs):
        entry_id = self.create_entry(content, mood=mood, title=title, **kwargs)
        if entry_id:
            return self.entries[entry_id].copy()
        return None

    def remove_entry(self, entry_id: str) -> bool:
        if not self.enabled or entry_id not in self.entries:
            return False
        try:
            del self.entries[entry_id]
            self._save_data()
            return True
        except:
            return False

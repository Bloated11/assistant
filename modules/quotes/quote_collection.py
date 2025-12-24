import logging
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import defaultdict
import uuid
import random

logger = logging.getLogger(__name__)

class QuoteCollection:
    def __init__(self, config: dict):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.storage_path = config.get('storage_path', 'data/quotes.json')
        
        self.quotes = {}
        self.authors = set()
        self.topics = set()
        self.collections = {}
        
        if self.enabled:
            self._load_data()
        
        logger.info("QuoteCollection initialized")
    
    def _load_data(self):
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.quotes = data.get('quotes', {})
                    self.authors = set(data.get('authors', []))
                    self.topics = set(data.get('topics', []))
                    self.collections = data.get('collections', {})
                logger.info(f"Loaded {len(self.quotes)} quotes")
        except Exception as e:
            logger.error(f"Error loading quote data: {e}")
    
    def _save_data(self):
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump({
                    'quotes': self.quotes,
                    'authors': list(self.authors),
                    'topics': list(self.topics),
                    'collections': self.collections,
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving quote data: {e}")
    
    def add_quote(self, text: str, author: str = "Unknown", source: str = None,
                 topics: List[str] = None, notes: str = "", favorite: bool = False) -> Optional[str]:
        if not self.enabled:
            return None
        
        try:
            quote_id = str(uuid.uuid4())[:8]
            
            self.authors.add(author)
            
            quote_topics = topics or []
            self.topics.update(quote_topics)
            
            self.quotes[quote_id] = {
                'id': quote_id,
                'text': text,
                'author': author,
                'source': source,
                'topics': quote_topics,
                'notes': notes,
                'favorite': favorite,
                'tags': [],
                'added_at': datetime.now().isoformat(),
                'last_viewed': None,
                'view_count': 0
            }
            
            self._save_data()
            logger.info(f"Added quote from {author}")
            return self.quotes[quote_id].copy()
            
        except Exception as e:
            logger.error(f"Error adding quote: {e}")
            return None
    
    def update_quote(self, quote_id: str, **updates) -> bool:
        if not self.enabled or quote_id not in self.quotes:
            return False
        
        try:
            for key, value in updates.items():
                if key in self.quotes[quote_id]:
                    self.quotes[quote_id][key] = value
            
            if 'author' in updates:
                self.authors.add(updates['author'])
            if 'topics' in updates:
                self.topics.update(updates['topics'])
            
            self._save_data()
            logger.info(f"Updated quote: {quote_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating quote: {e}")
            return False
    
    def delete_quote(self, quote_id: str) -> bool:
        if not self.enabled or quote_id not in self.quotes:
            return False
        
        try:
            del self.quotes[quote_id]
            self._save_data()
            logger.info(f"Deleted quote: {quote_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting quote: {e}")
            return False
    
    def toggle_favorite(self, quote_id: str) -> bool:
        if not self.enabled or quote_id not in self.quotes:
            return False
        
        try:
            self.quotes[quote_id]['favorite'] = not self.quotes[quote_id]['favorite']
            self._save_data()
            return True
            
        except Exception as e:
            logger.error(f"Error toggling favorite: {e}")
            return False
    
    def create_collection(self, name: str, description: str = "") -> Optional[str]:
        if not self.enabled:
            return None
        
        try:
            collection_id = str(uuid.uuid4())[:8]
            
            self.collections[collection_id] = {
                'id': collection_id,
                'name': name,
                'description': description,
                'quote_ids': [],
                'created_at': datetime.now().isoformat()
            }
            
            self._save_data()
            logger.info(f"Created collection: {name}")
            return collection_id
            
        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            return None
    
    def add_to_collection(self, collection_id: str, quote_id: str) -> bool:
        if not self.enabled or collection_id not in self.collections or quote_id not in self.quotes:
            return False
        
        try:
            if quote_id not in self.collections[collection_id]['quote_ids']:
                self.collections[collection_id]['quote_ids'].append(quote_id)
                self._save_data()
            return True
            
        except Exception as e:
            logger.error(f"Error adding to collection: {e}")
            return False
    
    def get_quote(self, quote_id: str) -> Optional[Dict[str, Any]]:
        quote = self.quotes.get(quote_id)
        if quote:
            quote['view_count'] += 1
            quote['last_viewed'] = datetime.now().isoformat()
            self._save_data()
        return quote
    
    def list_quotes(self, author: str = None, topic: str = None, 
                   favorite: bool = None) -> List[Dict[str, Any]]:
        quotes = list(self.quotes.values())
        
        if author:
            quotes = [q for q in quotes if q.get('author', '').lower() == author.lower()]
        if topic:
            quotes = [q for q in quotes if topic in q.get('topics', [])]
        if favorite is not None:
            quotes = [q for q in quotes if q.get('favorite') == favorite]
        
        return sorted(quotes, key=lambda x: x.get('added_at', ''), reverse=True)
    
    def search_quotes(self, query: str) -> List[Dict[str, Any]]:
        query_lower = query.lower()
        results = []
        
        for quote in self.quotes.values():
            if (query_lower in quote['text'].lower() or
                query_lower in quote.get('author', '').lower() or
                query_lower in quote.get('source', '').lower() or
                query_lower in ' '.join(quote.get('topics', [])).lower()):
                results.append(quote)
        
        return results
    
    def get_random_quote(self, author: str = None, topic: str = None) -> Optional[Dict[str, Any]]:
        quotes = self.list_quotes(author=author, topic=topic)
        if quotes:
            return random.choice(quotes)
        return None
    
    def get_quote_of_the_day(self) -> Optional[Dict[str, Any]]:
        if not self.quotes:
            return None
        
        day_seed = datetime.now().date().isoformat()
        random.seed(day_seed)
        quote = random.choice(list(self.quotes.values()))
        random.seed()
        
        return quote
    
    def get_favorites(self) -> List[Dict[str, Any]]:
        return [q for q in self.quotes.values() if q.get('favorite', False)]
    
    def get_quotes_by_author(self, author: str) -> List[Dict[str, Any]]:
        return [q for q in self.quotes.values() if q.get('author', '').lower() == author.lower()]
    
    def get_quotes_by_topic(self, topic: str) -> List[Dict[str, Any]]:
        return [q for q in self.quotes.values() if topic in q.get('topics', [])]
    
    def get_collection(self, collection_id: str) -> Optional[Dict[str, Any]]:
        if collection_id not in self.collections:
            return None
        
        collection = self.collections[collection_id].copy()
        collection['quotes'] = [self.quotes[qid] for qid in collection['quote_ids'] if qid in self.quotes]
        return collection
    
    def list_collections(self) -> List[Dict[str, Any]]:
        return list(self.collections.values())
    
    def get_stats(self) -> Dict[str, Any]:
        total_quotes = len(self.quotes)
        total_authors = len(self.authors)
        total_topics = len(self.topics)
        favorites = sum(1 for q in self.quotes.values() if q.get('favorite', False))
        
        by_author = defaultdict(int)
        by_topic = defaultdict(int)
        
        for quote in self.quotes.values():
            by_author[quote.get('author', 'Unknown')] += 1
            for topic in quote.get('topics', []):
                by_topic[topic] += 1
        
        most_viewed = sorted(self.quotes.values(), key=lambda x: x.get('view_count', 0), reverse=True)[:5]
        
        return {
            'total_quotes': total_quotes,
            'total_authors': total_authors,
            'total_topics': total_topics,
            'favorites': favorites,
            'total_collections': len(self.collections),
            'top_authors': dict(sorted(by_author.items(), key=lambda x: x[1], reverse=True)[:10]),
            'top_topics': dict(sorted(by_topic.items(), key=lambda x: x[1], reverse=True)[:10]),
            'most_viewed': [{'id': q['id'], 'author': q['author'], 'views': q['view_count']} for q in most_viewed]
        }
    def get_all_quotes(self):
        return self.list_quotes()

    
    

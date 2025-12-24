import logging
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class ReadingListManager:
    def __init__(self, config: dict):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.storage_path = config.get('storage_path', 'data/reading_list.json')
        
        self.books = {}
        self.reading_sessions = {}
        self.reading_goals = {}
        
        if self.enabled:
            self._load_data()
        
        logger.info("ReadingListManager initialized")
    
    def _load_data(self):
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.books = data.get('books', {})
                    self.reading_sessions = data.get('reading_sessions', {})
                    self.reading_goals = data.get('reading_goals', {})
                logger.info(f"Loaded {len(self.books)} books")
        except Exception as e:
            logger.error(f"Error loading reading list: {e}")
    
    def _save_data(self):
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump({
                    'books': self.books,
                    'reading_sessions': self.reading_sessions,
                    'reading_goals': self.reading_goals,
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving reading list: {e}")
    
    def add_book(self, title: str, author: str, pages: int = None, genre: str = None,
                isbn: str = None, status: str = "to_read", notes: str = "") -> Optional[str]:
        if not self.enabled:
            return None
        
        try:
            book_id = str(uuid.uuid4())[:8]
            
            self.books[book_id] = {
                'id': book_id,
                'title': title,
                'author': author,
                'pages': pages,
                'current_page': 0,
                'genre': genre,
                'isbn': isbn,
                'status': status,
                'notes': notes,
                'rating': None,
                'review': "",
                'added_at': datetime.now().isoformat(),
                'started_at': None,
                'finished_at': None,
                'tags': []
            }
            
            self._save_data()
            logger.info(f"Added book: {title} by {author}")
            return self.books[book_id].copy()
            
        except Exception as e:
            logger.error(f"Error adding book: {e}")
            return None
    
    def update_book_status(self, book_id: str, status: str) -> bool:
        if not self.enabled or book_id not in self.books:
            return False
        
        try:
            self.books[book_id]['status'] = status
            
            if status == 'reading' and not self.books[book_id]['started_at']:
                self.books[book_id]['started_at'] = datetime.now().isoformat()
            elif status == 'finished':
                self.books[book_id]['finished_at'] = datetime.now().isoformat()
                if self.books[book_id]['pages']:
                    self.books[book_id]['current_page'] = self.books[book_id]['pages']
            
            self._save_data()
            logger.info(f"Updated book {book_id} status to {status}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating book status: {e}")
            return False
    
    def update_progress(self, book_id: str, current_page: int) -> bool:
        if not self.enabled or book_id not in self.books:
            return False
        
        try:
            self.books[book_id]['current_page'] = int(current_page)
            
            if self.books[book_id]['status'] == 'to_read':
                self.books[book_id]['status'] = 'reading'
                self.books[book_id]['started_at'] = datetime.now().isoformat()
            
            if self.books[book_id]['pages'] and current_page >= self.books[book_id]['pages']:
                self.books[book_id]['status'] = 'finished'
                self.books[book_id]['finished_at'] = datetime.now().isoformat()
            
            self._save_data()
            logger.info(f"Updated progress for book {book_id}: page {current_page}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating progress: {e}")
            return False
    
    def rate_book(self, book_id: str, rating: int, review: str = "") -> bool:
        if not self.enabled or book_id not in self.books:
            return False
        
        try:
            self.books[book_id]['rating'] = max(1, min(5, int(rating)))
            if review:
                self.books[book_id]['review'] = review
            
            self._save_data()
            logger.info(f"Rated book {book_id}: {rating}/5")
            return True
            
        except Exception as e:
            logger.error(f"Error rating book: {e}")
            return False
    
    def log_reading_session(self, book_id: str, duration: int, pages_read: int = None,
                           notes: str = "") -> Optional[str]:
        if not self.enabled or book_id not in self.books:
            return None
        
        try:
            session_id = str(uuid.uuid4())[:8]
            
            self.reading_sessions[session_id] = {
                'id': session_id,
                'book_id': book_id,
                'duration': duration,
                'pages_read': pages_read,
                'notes': notes,
                'date': datetime.now().isoformat()
            }
            
            if pages_read:
                current = self.books[book_id]['current_page']
                self.update_progress(book_id, current + pages_read)
            
            self._save_data()
            logger.info(f"Logged reading session: {duration} minutes")
            return session_id
            
        except Exception as e:
            logger.error(f"Error logging reading session: {e}")
            return None
    
    def set_reading_goal(self, goal_type: str, target_value: int, 
                        deadline: str = None) -> Optional[str]:
        if not self.enabled:
            return None
        
        try:
            goal_id = str(uuid.uuid4())[:8]
            
            self.reading_goals[goal_id] = {
                'id': goal_id,
                'type': goal_type,
                'target_value': int(target_value),
                'current_value': 0,
                'deadline': deadline,
                'created_at': datetime.now().isoformat(),
                'status': 'active'
            }
            
            self._save_data()
            logger.info(f"Set reading goal: {goal_type} = {target_value}")
            return goal_id
            
        except Exception as e:
            logger.error(f"Error setting reading goal: {e}")
            return None
    
    def get_book(self, book_id: str) -> Optional[Dict[str, Any]]:
        if not self.enabled or book_id not in self.books:
            return None
        
        book = self.books[book_id].copy()
        if book['pages'] and book['current_page']:
            book['progress_percentage'] = (book['current_page'] / book['pages']) * 100
        else:
            book['progress_percentage'] = 0
        
        return book
    
    def search_books(self, query: str = None, status: str = None, 
                    genre: str = None, author: str = None) -> List[Dict[str, Any]]:
        if not self.enabled:
            return []
        
        try:
            results = list(self.books.values())
            
            if query:
                query_lower = query.lower()
                results = [b for b in results if query_lower in b['title'].lower() 
                          or query_lower in b['author'].lower()]
            
            if status:
                results = [b for b in results if b['status'] == status]
            
            if genre:
                results = [b for b in results if b.get('genre') == genre]
            
            if author:
                results = [b for b in results if author.lower() in b['author'].lower()]
            
            for book in results:
                if book['pages'] and book['current_page']:
                    book['progress_percentage'] = (book['current_page'] / book['pages']) * 100
                else:
                    book['progress_percentage'] = 0
            
            return sorted(results, key=lambda x: x['added_at'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error searching books: {e}")
            return []
    
    def get_reading_stats(self) -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None
        
        try:
            total_books = len(self.books)
            finished_books = len([b for b in self.books.values() if b['status'] == 'finished'])
            reading_books = len([b for b in self.books.values() if b['status'] == 'reading'])
            to_read_books = len([b for b in self.books.values() if b['status'] == 'to_read'])
            
            total_pages_read = sum(b['current_page'] for b in self.books.values() 
                                  if b['current_page'])
            
            avg_rating = None
            rated_books = [b for b in self.books.values() if b['rating']]
            if rated_books:
                avg_rating = sum(b['rating'] for b in rated_books) / len(rated_books)
            
            genres = {}
            for book in self.books.values():
                if book.get('genre'):
                    genres[book['genre']] = genres.get(book['genre'], 0) + 1
            
            return {
                'total_books': total_books,
                'finished': finished_books,
                'reading': reading_books,
                'to_read': to_read_books,
                'total_pages_read': total_pages_read,
                'avg_rating': avg_rating,
                'genres': genres,
                'total_sessions': len(self.reading_sessions)
            }
            
        except Exception as e:
            logger.error(f"Error getting reading stats: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            'enabled': self.enabled,
            'total_books': len(self.books),
            'total_sessions': len(self.reading_sessions),
            'active_goals': len([g for g in self.reading_goals.values() if g['status'] == 'active'])
        }

    def get_all_books(self):
        return self.list_books()

    
    def delete_book(self, book_id: str) -> bool:
        return self.remove_item(book_id)

    def list_books(self, **kwargs):
        return self.search_books(**kwargs)

    def remove_item(self, book_id: str) -> bool:
        if book_id in self.books:
            del self.books[book_id]
            self._save_data()
            return True
        return False


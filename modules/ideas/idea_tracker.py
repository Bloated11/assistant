import logging
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import defaultdict
import uuid

logger = logging.getLogger(__name__)

class IdeaTracker:
    def __init__(self, config: dict):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.storage_path = config.get('storage_path', 'data/ideas.json')
        
        self.ideas = {}
        self.boards = {}
        self.tags = set()
        
        if self.enabled:
            self._load_data()
        
        logger.info("IdeaTracker initialized")
    
    def _load_data(self):
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.ideas = data.get('ideas', {})
                    self.boards = data.get('boards', {})
                    self.tags = set(data.get('tags', []))
                logger.info(f"Loaded {len(self.ideas)} ideas")
        except Exception as e:
            logger.error(f"Error loading ideas: {e}")
    
    def _save_data(self):
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump({
                    'ideas': self.ideas,
                    'boards': self.boards,
                    'tags': list(self.tags),
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving ideas: {e}")
    
    def add_idea(self, title: str, description: str = "", category: str = None,
                tags: List[str] = None, board_id: str = None, priority: str = "medium") -> Optional[str]:
        if not self.enabled:
            return None
        
        try:
            idea_id = str(uuid.uuid4())[:8]
            
            idea_tags = tags or []
            self.tags.update(idea_tags)
            
            self.ideas[idea_id] = {
                'id': idea_id,
                'title': title,
                'description': description,
                'category': category,
                'tags': idea_tags,
                'board_id': board_id,
                'priority': priority,
                'status': 'new',
                'notes': [],
                'related_ideas': [],
                'rating': None,
                'feasibility': None,
                'impact': None,
                'effort': None,
                'favorite': False,
                'archived': False,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            self._save_data()
            logger.info(f"Added idea: {title}")
            return self.ideas[idea_id].copy()
            
        except Exception as e:
            logger.error(f"Error adding idea: {e}")
            return None
    
    def create_board(self, name: str, description: str = "", color: str = None) -> Optional[str]:
        if not self.enabled:
            return None
        
        try:
            board_id = str(uuid.uuid4())[:8]
            
            self.boards[board_id] = {
                'id': board_id,
                'name': name,
                'description': description,
                'color': color,
                'created_at': datetime.now().isoformat()
            }
            
            self._save_data()
            logger.info(f"Created idea board: {name}")
            return board_id
            
        except Exception as e:
            logger.error(f"Error creating board: {e}")
            return None
    
    def add_note_to_idea(self, idea_id: str, note: str) -> bool:
        if not self.enabled or idea_id not in self.ideas:
            return False
        
        try:
            note_entry = {
                'id': str(uuid.uuid4())[:8],
                'content': note,
                'created_at': datetime.now().isoformat()
            }
            
            self.ideas[idea_id]['notes'].append(note_entry)
            self.ideas[idea_id]['updated_at'] = datetime.now().isoformat()
            self._save_data()
            logger.info(f"Added note to idea: {idea_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding note: {e}")
            return False
    
    def rate_idea(self, idea_id: str, rating: int, feasibility: str = None,
                 impact: str = None, effort: str = None) -> bool:
        if not self.enabled or idea_id not in self.ideas:
            return False
        
        try:
            self.ideas[idea_id]['rating'] = max(1, min(10, rating))
            if feasibility:
                self.ideas[idea_id]['feasibility'] = feasibility
            if impact:
                self.ideas[idea_id]['impact'] = impact
            if effort:
                self.ideas[idea_id]['effort'] = effort
            
            self.ideas[idea_id]['updated_at'] = datetime.now().isoformat()
            self._save_data()
            logger.info(f"Rated idea {idea_id}: {rating}/10")
            return True
            
        except Exception as e:
            logger.error(f"Error rating idea: {e}")
            return False
    
    def update_idea_status(self, idea_id: str, status: str) -> bool:
        if not self.enabled or idea_id not in self.ideas:
            return False
        
        try:
            valid_statuses = ['new', 'exploring', 'in_progress', 'implemented', 'abandoned']
            if status not in valid_statuses:
                return False
            
            self.ideas[idea_id]['status'] = status
            self.ideas[idea_id]['updated_at'] = datetime.now().isoformat()
            self._save_data()
            logger.info(f"Updated idea {idea_id} status to: {status}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating idea status: {e}")
            return False
    
    def link_ideas(self, idea_id1: str, idea_id2: str) -> bool:
        if not self.enabled or idea_id1 not in self.ideas or idea_id2 not in self.ideas:
            return False
        
        try:
            if idea_id2 not in self.ideas[idea_id1]['related_ideas']:
                self.ideas[idea_id1]['related_ideas'].append(idea_id2)
            if idea_id1 not in self.ideas[idea_id2]['related_ideas']:
                self.ideas[idea_id2]['related_ideas'].append(idea_id1)
            
            self._save_data()
            logger.info(f"Linked ideas: {idea_id1} <-> {idea_id2}")
            return True
            
        except Exception as e:
            logger.error(f"Error linking ideas: {e}")
            return False
    
    def toggle_favorite(self, idea_id: str) -> bool:
        if not self.enabled or idea_id not in self.ideas:
            return False
        
        try:
            self.ideas[idea_id]['favorite'] = not self.ideas[idea_id]['favorite']
            self.ideas[idea_id]['updated_at'] = datetime.now().isoformat()
            self._save_data()
            return True
            
        except Exception as e:
            logger.error(f"Error toggling favorite: {e}")
            return False
    
    def archive_idea(self, idea_id: str, archived: bool = True) -> bool:
        if not self.enabled or idea_id not in self.ideas:
            return False
        
        try:
            self.ideas[idea_id]['archived'] = archived
            self.ideas[idea_id]['updated_at'] = datetime.now().isoformat()
            self._save_data()
            logger.info(f"Idea {idea_id} archived: {archived}")
            return True
            
        except Exception as e:
            logger.error(f"Error archiving idea: {e}")
            return False
    
    def get_idea(self, idea_id: str) -> Optional[Dict[str, Any]]:
        return self.ideas.get(idea_id)
    
    def list_ideas(self, category: str = None, board_id: str = None,
                  status: str = None, archived: bool = False) -> List[Dict[str, Any]]:
        ideas = list(self.ideas.values())
        
        if not archived:
            ideas = [i for i in ideas if not i.get('archived', False)]
        
        if category:
            ideas = [i for i in ideas if i.get('category') == category]
        if board_id:
            ideas = [i for i in ideas if i.get('board_id') == board_id]
        if status:
            ideas = [i for i in ideas if i.get('status') == status]
        
        return sorted(ideas, key=lambda x: x.get('created_at', ''), reverse=True)
    
    def get_favorites(self) -> List[Dict[str, Any]]:
        return [i for i in self.ideas.values() if i.get('favorite', False) and not i.get('archived', False)]
    
    def search_ideas(self, query: str) -> List[Dict[str, Any]]:
        query_lower = query.lower()
        results = []
        
        for idea in self.ideas.values():
            if idea.get('archived', False):
                continue
            
            if (query_lower in idea['title'].lower() or
                query_lower in idea.get('description', '').lower() or
                query_lower in ' '.join(idea.get('tags', [])).lower()):
                results.append(idea)
        
        return results
    
    def get_ideas_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        return [i for i in self.ideas.values() if tag in i.get('tags', []) and not i.get('archived', False)]
    
    def get_top_rated_ideas(self, limit: int = 10) -> List[Dict[str, Any]]:
        rated_ideas = [i for i in self.ideas.values() if i.get('rating') and not i.get('archived', False)]
        return sorted(rated_ideas, key=lambda x: x.get('rating', 0), reverse=True)[:limit]
    
    def get_board(self, board_id: str) -> Optional[Dict[str, Any]]:
        return self.boards.get(board_id)
    
    def list_boards(self) -> List[Dict[str, Any]]:
        return list(self.boards.values())
    
    def get_board_ideas(self, board_id: str) -> List[Dict[str, Any]]:
        return [i for i in self.ideas.values() if i.get('board_id') == board_id and not i.get('archived', False)]
    
    def get_stats(self) -> Dict[str, Any]:
        total_ideas = len(self.ideas)
        active_ideas = sum(1 for i in self.ideas.values() if not i.get('archived', False))
        archived_ideas = sum(1 for i in self.ideas.values() if i.get('archived', False))
        favorites = sum(1 for i in self.ideas.values() if i.get('favorite', False))
        
        by_status = defaultdict(int)
        by_category = defaultdict(int)
        
        for idea in self.ideas.values():
            if not idea.get('archived', False):
                by_status[idea.get('status', 'new')] += 1
                if idea.get('category'):
                    by_category[idea['category']] += 1
        
        avg_rating = None
        rated_ideas = [i for i in self.ideas.values() if i.get('rating')]
        if rated_ideas:
            avg_rating = sum(i['rating'] for i in rated_ideas) / len(rated_ideas)
        
        return {
            'total_ideas': total_ideas,
            'active_ideas': active_ideas,
            'archived_ideas': archived_ideas,
            'favorites': favorites,
            'total_boards': len(self.boards),
            'total_tags': len(self.tags),
            'by_status': dict(by_status),
            'by_category': dict(by_category),
            'avg_rating': round(avg_rating, 2) if avg_rating else None,
            'rated_ideas': len(rated_ideas)
        }
    def get_all_ideas(self):
        return self.list_ideas()

    
    
    def delete_idea(self, idea_id: str) -> bool:
        if not self.enabled or idea_id not in self.ideas:
            return False
        del self.ideas[idea_id]
        self._save_data()
        return True

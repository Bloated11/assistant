import logging
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class NotesManager:
    def __init__(self, config: dict):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.storage_path = config.get('storage_path', 'data/notes.json')
        self.templates_path = config.get('templates_path', 'data/note_templates.json')
        
        self.notes = {}
        self.templates = {}
        self.tags = set()
        
        if self.enabled:
            self._load_notes()
            self._load_templates()
        
        logger.info("NotesManager initialized")
    
    def _load_notes(self):
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.notes = data.get('notes', {})
                    self.tags = set(data.get('tags', []))
                logger.info(f"Loaded {len(self.notes)} notes")
        except Exception as e:
            logger.error(f"Error loading notes: {e}")
    
    def _save_notes(self):
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump({
                    'notes': self.notes,
                    'tags': list(self.tags),
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving notes: {e}")
    
    def _load_templates(self):
        try:
            if os.path.exists(self.templates_path):
                with open(self.templates_path, 'r') as f:
                    self.templates = json.load(f)
        except Exception as e:
            logger.error(f"Error loading templates: {e}")
    
    def _save_templates(self):
        try:
            os.makedirs(os.path.dirname(self.templates_path), exist_ok=True)
            with open(self.templates_path, 'w') as f:
                json.dump(self.templates, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving templates: {e}")
    
    def create_note(self, title: str, content: str, tags: List[str] = None, 
                   category: str = None, template: str = None) -> Optional[str]:
        if not self.enabled:
            return None
        
        try:
            note_id = str(uuid.uuid4())[:8]
            
            if template and template in self.templates:
                content = self.templates[template]['content'] + "\n\n" + content
            
            note_tags = tags or []
            self.tags.update(note_tags)
            
            self.notes[note_id] = {
                'id': note_id,
                'title': title,
                'content': content,
                'tags': note_tags,
                'category': category,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'pinned': False,
                'archived': False
            }
            
            self._save_notes()
            logger.info(f"Created note: {title}")
            return self.notes[note_id].copy()
            
        except Exception as e:
            logger.error(f"Error creating note: {e}")
            return None
    
    def quick_note(self, content: str) -> Optional[str]:
        if not self.enabled:
            return None
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        title = f"Quick Note - {timestamp}"
        
        return self.create_note(title, content, tags=['quick'])
    
    def update_note(self, note_id: str, title: str = None, content: str = None, 
                   tags: List[str] = None, category: str = None) -> bool:
        if not self.enabled:
            return False
        
        try:
            if note_id not in self.notes:
                logger.warning(f"Note {note_id} not found")
                return False
            
            note = self.notes[note_id]
            
            if title:
                note['title'] = title
            if content is not None:
                note['content'] = content
            if tags is not None:
                note['tags'] = tags
                self.tags.update(tags)
            if category is not None:
                note['category'] = category
            
            note['updated_at'] = datetime.now().isoformat()
            self._save_notes()
            
            logger.info(f"Updated note: {note_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating note: {e}")
            return False
    
    def append_to_note(self, note_id: str, content: str) -> bool:
        if not self.enabled:
            return False
        
        try:
            if note_id not in self.notes:
                return False
            
            note = self.notes[note_id]
            note['content'] += f"\n\n{content}"
            note['updated_at'] = datetime.now().isoformat()
            self._save_notes()
            
            return True
            
        except Exception as e:
            logger.error(f"Error appending to note: {e}")
            return False
    
    def get_note(self, note_id: str) -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None
        
        return self.notes.get(note_id)
    
    def search_notes(self, query: str = None, tags: List[str] = None, 
                    category: str = None, pinned_only: bool = False) -> List[Dict[str, Any]]:
        if not self.enabled:
            return []
        
        results = []
        query_lower = query.lower() if query else None
        
        for note_id, note in self.notes.items():
            if note.get('archived'):
                continue
            
            if pinned_only and not note.get('pinned'):
                continue
            
            if category and note.get('category') != category:
                continue
            
            if tags:
                if not all(tag in note.get('tags', []) for tag in tags):
                    continue
            
            if query_lower:
                title_match = query_lower in note['title'].lower()
                content_match = query_lower in note['content'].lower()
                if not (title_match or content_match):
                    continue
            
            results.append({
                'id': note['id'],
                'title': note['title'],
                'preview': note['content'][:100] + '...' if len(note['content']) > 100 else note['content'],
                'tags': note.get('tags', []),
                'category': note.get('category'),
                'pinned': note.get('pinned', False),
                'created_at': note['created_at'],
                'updated_at': note['updated_at']
            })
        
        results.sort(key=lambda x: (not x['pinned'], x['updated_at']), reverse=True)
        return results
    
    def list_notes(self, limit: int = 20, category: str = None, 
                  pinned_only: bool = False, archived: bool = False) -> List[Dict[str, Any]]:
        if not self.enabled:
            return []
        
        notes_list = []
        
        for note_id, note in self.notes.items():
            if archived != note.get('archived', False):
                continue
            
            if pinned_only and not note.get('pinned'):
                continue
            
            if category and note.get('category') != category:
                continue
            
            notes_list.append({
                'id': note['id'],
                'title': note['title'],
                'tags': note.get('tags', []),
                'category': note.get('category'),
                'pinned': note.get('pinned', False),
                'updated_at': note['updated_at']
            })
        
        notes_list.sort(key=lambda x: (not x['pinned'], x['updated_at']), reverse=True)
        return notes_list[:limit]
    
    def pin_note(self, note_id: str) -> bool:
        if not self.enabled or note_id not in self.notes:
            return False
        
        self.notes[note_id]['pinned'] = True
        self._save_notes()
        return True
    
    def unpin_note(self, note_id: str) -> bool:
        if not self.enabled or note_id not in self.notes:
            return False
        
        self.notes[note_id]['pinned'] = False
        self._save_notes()
        return True
    
    def archive_note(self, note_id: str) -> bool:
        if not self.enabled or note_id not in self.notes:
            return False
        
        self.notes[note_id]['archived'] = True
        self._save_notes()
        logger.info(f"Archived note: {note_id}")
        return True
    
    def unarchive_note(self, note_id: str) -> bool:
        if not self.enabled or note_id not in self.notes:
            return False
        
        self.notes[note_id]['archived'] = False
        self._save_notes()
        return True
    
    def delete_note(self, note_id: str) -> bool:
        if not self.enabled or note_id not in self.notes:
            return False
        
        del self.notes[note_id]
        self._save_notes()
        logger.info(f"Deleted note: {note_id}")
        return True
    
    def create_template(self, name: str, content: str, description: str = "") -> bool:
        if not self.enabled:
            return False
        
        try:
            self.templates[name] = {
                'name': name,
                'content': content,
                'description': description,
                'created_at': datetime.now().isoformat()
            }
            
            self._save_templates()
            logger.info(f"Created template: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating template: {e}")
            return False
    
    def list_templates(self) -> List[Dict[str, Any]]:
        if not self.enabled:
            return []
        
        return [
            {
                'name': template['name'],
                'description': template.get('description', ''),
                'created_at': template['created_at']
            }
            for template in self.templates.values()
        ]
    
    def get_tags(self) -> List[str]:
        if not self.enabled:
            return []
        
        return sorted(list(self.tags))
    
    def get_categories(self) -> List[str]:
        if not self.enabled:
            return []
        
        categories = set()
        for note in self.notes.values():
            if note.get('category'):
                categories.add(note['category'])
        
        return sorted(list(categories))
    
    def find_note_by_title(self, title: str) -> Optional[str]:
        title_lower = title.lower()
        for note_id, note in self.notes.items():
            if note['title'].lower() == title_lower:
                return note_id
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        if not self.enabled:
            return {'enabled': False}
        
        total_notes = len(self.notes)
        active_notes = sum(1 for n in self.notes.values() if not n.get('archived'))
        archived_notes = sum(1 for n in self.notes.values() if n.get('archived'))
        pinned_notes = sum(1 for n in self.notes.values() if n.get('pinned') and not n.get('archived'))
        
        total_tags = len(self.tags)
        total_categories = len(self.get_categories())
        
        return {
            'enabled': True,
            'total_notes': total_notes,
            'active_notes': active_notes,
            'archived_notes': archived_notes,
            'pinned_notes': pinned_notes,
            'total_tags': total_tags,
            'total_categories': total_categories,
            'total_templates': len(self.templates)
        }
    def get_all_notes(self):
        return self.list_notes()

    
    def get_all_notes(self) -> List[Dict[str, Any]]:
        notes_list = []
        for note_id, note in self.notes.items():
            note_copy = note.copy()
            note_copy['id'] = note_id
            notes_list.append(note_copy)
        return notes_list
    
    def remove_note(self, note_id: str) -> bool:
        if not self.enabled or note_id not in self.notes:
            return False
        try:
            del self.notes[note_id]
            self._save_notes()
            return True
        except:
            return False
    
    def delete_note(self, note_id: str) -> bool:
        return self.remove_note(note_id)


    def add_note(self, title: str, content: str, tags: list = None) -> Dict[str, Any]:
        note_id = self.create_note(title, content, tags or [])
        if note_id:
            return self.notes[note_id].copy()
        return None

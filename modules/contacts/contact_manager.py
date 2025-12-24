import logging
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import uuid

logger = logging.getLogger(__name__)

class ContactManager:
    def __init__(self, config: dict):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.storage_path = config.get('storage_path', 'data/contacts.json')
        
        self.contacts = {}
        self.groups = {}
        self.interaction_history = {}
        
        if self.enabled:
            self._load_data()
        
        logger.info("ContactManager initialized")
    
    def _load_data(self):
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.contacts = data.get('contacts', {})
                    self.groups = data.get('groups', {})
                    self.interaction_history = data.get('interaction_history', {})
                logger.info(f"Loaded {len(self.contacts)} contacts")
        except Exception as e:
            logger.error(f"Error loading contacts: {e}")
    
    def _save_data(self):
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump({
                    'contacts': self.contacts,
                    'groups': self.groups,
                    'interaction_history': self.interaction_history,
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving contacts: {e}")
    
    def add_contact(self, name: str, email: str = None, phone: str = None,
                   company: str = None, title: str = None, address: str = None,
                   birthday: str = None, notes: str = "", tags: List[str] = None) -> Optional[str]:
        if not self.enabled:
            return None
        
        try:
            contact_id = str(uuid.uuid4())[:8]
            
            self.contacts[contact_id] = {
                'id': contact_id,
                'name': name,
                'email': email,
                'phone': phone,
                'company': company,
                'title': title,
                'address': address,
                'birthday': birthday,
                'notes': notes,
                'tags': tags or [],
                'favorite': False,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'last_contacted': None,
                'social_media': {}
            }
            
            self._save_data()
            logger.info(f"Added contact: {name}")
            return self.contacts[contact_id].copy()
            
        except Exception as e:
            logger.error(f"Error adding contact: {e}")
            return None
    
    def update_contact(self, contact_id: str, **kwargs) -> bool:
        if not self.enabled or contact_id not in self.contacts:
            return False
        
        try:
            allowed_fields = ['name', 'email', 'phone', 'company', 'title', 
                            'address', 'birthday', 'notes', 'tags']
            
            for field, value in kwargs.items():
                if field in allowed_fields and value is not None:
                    self.contacts[contact_id][field] = value
            
            self.contacts[contact_id]['updated_at'] = datetime.now().isoformat()
            
            self._save_data()
            logger.info(f"Updated contact: {contact_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating contact: {e}")
            return False
    
    def get_contact(self, contact_id: str) -> Optional[Dict[str, Any]]:
        if not self.enabled or contact_id not in self.contacts:
            return None
        
        contact = self.contacts[contact_id].copy()
        
        interactions = [i for i in self.interaction_history.values() 
                       if i['contact_id'] == contact_id]
        contact['interaction_count'] = len(interactions)
        
        if interactions:
            latest = max(interactions, key=lambda x: x['date'])
            contact['last_interaction'] = latest
        
        return contact
    
    def search_contacts(self, query: str = None, tag: str = None, 
                       company: str = None) -> List[Dict[str, Any]]:
        if not self.enabled:
            return []
        
        try:
            results = list(self.contacts.values())
            
            if query:
                query_lower = query.lower()
                results = [c for c in results if query_lower in c['name'].lower() 
                          or (c.get('email') and query_lower in c['email'].lower())
                          or (c.get('phone') and query_lower in c['phone'])]
            
            if tag:
                results = [c for c in results if tag in c.get('tags', [])]
            
            if company:
                results = [c for c in results if c.get('company') == company]
            
            return sorted(results, key=lambda x: x['name'])
            
        except Exception as e:
            logger.error(f"Error searching contacts: {e}")
            return []
    
    def delete_contact(self, contact_id: str) -> bool:
        if not self.enabled or contact_id not in self.contacts:
            return False
        
        try:
            del self.contacts[contact_id]
            
            self.interaction_history = {k: v for k, v in self.interaction_history.items() 
                                       if v['contact_id'] != contact_id}
            
            self._save_data()
            logger.info(f"Deleted contact: {contact_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting contact: {e}")
            return False
    
    def toggle_favorite(self, contact_id: str) -> bool:
        if not self.enabled or contact_id not in self.contacts:
            return False
        
        try:
            self.contacts[contact_id]['favorite'] = not self.contacts[contact_id]['favorite']
            self._save_data()
            return True
            
        except Exception as e:
            logger.error(f"Error toggling favorite: {e}")
            return False
    
    def create_group(self, name: str, description: str = "") -> Optional[str]:
        if not self.enabled:
            return None
        
        try:
            group_id = str(uuid.uuid4())[:8]
            
            self.groups[group_id] = {
                'id': group_id,
                'name': name,
                'description': description,
                'members': [],
                'created_at': datetime.now().isoformat()
            }
            
            self._save_data()
            logger.info(f"Created group: {name}")
            return group_id
            
        except Exception as e:
            logger.error(f"Error creating group: {e}")
            return None
    
    def add_to_group(self, group_id: str, contact_id: str) -> bool:
        if not self.enabled or group_id not in self.groups or contact_id not in self.contacts:
            return False
        
        try:
            if contact_id not in self.groups[group_id]['members']:
                self.groups[group_id]['members'].append(contact_id)
                self._save_data()
                logger.info(f"Added contact {contact_id} to group {group_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error adding to group: {e}")
            return False
    
    def log_interaction(self, contact_id: str, interaction_type: str, 
                       notes: str = "", date: str = None) -> Optional[str]:
        if not self.enabled or contact_id not in self.contacts:
            return None
        
        try:
            interaction_id = str(uuid.uuid4())[:8]
            interaction_date = date or datetime.now().isoformat()
            
            self.interaction_history[interaction_id] = {
                'id': interaction_id,
                'contact_id': contact_id,
                'type': interaction_type,
                'notes': notes,
                'date': interaction_date
            }
            
            self.contacts[contact_id]['last_contacted'] = interaction_date
            
            self._save_data()
            logger.info(f"Logged interaction with contact {contact_id}")
            return interaction_id
            
        except Exception as e:
            logger.error(f"Error logging interaction: {e}")
            return None
    
    def get_upcoming_birthdays(self, days: int = 30) -> List[Dict[str, Any]]:
        if not self.enabled:
            return []
        
        try:
            today = datetime.now().date()
            upcoming = []
            
            for contact in self.contacts.values():
                if not contact.get('birthday'):
                    continue
                
                try:
                    bday = datetime.fromisoformat(contact['birthday']).date()
                    
                    this_year_bday = bday.replace(year=today.year)
                    if this_year_bday < today:
                        this_year_bday = bday.replace(year=today.year + 1)
                    
                    days_until = (this_year_bday - today).days
                    
                    if 0 <= days_until <= days:
                        upcoming.append({
                            'contact_id': contact['id'],
                            'name': contact['name'],
                            'birthday': contact['birthday'],
                            'days_until': days_until,
                            'date': this_year_bday.isoformat()
                        })
                except:
                    continue
            
            return sorted(upcoming, key=lambda x: x['days_until'])
            
        except Exception as e:
            logger.error(f"Error getting upcoming birthdays: {e}")
            return []
    
    def get_neglected_contacts(self, days: int = 90) -> List[Dict[str, Any]]:
        if not self.enabled:
            return []
        
        try:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            neglected = []
            
            for contact in self.contacts.values():
                last_contact = contact.get('last_contacted')
                
                if not last_contact or last_contact < cutoff:
                    days_since = None
                    if last_contact:
                        days_since = (datetime.now() - datetime.fromisoformat(last_contact)).days
                    
                    neglected.append({
                        'contact_id': contact['id'],
                        'name': contact['name'],
                        'last_contacted': last_contact,
                        'days_since': days_since
                    })
            
            return sorted(neglected, key=lambda x: x.get('days_since') or 99999, reverse=True)
            
        except Exception as e:
            logger.error(f"Error getting neglected contacts: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            'enabled': self.enabled,
            'total_contacts': len(self.contacts),
            'total_groups': len(self.groups),
            'favorite_contacts': len([c for c in self.contacts.values() if c['favorite']]),
            'total_interactions': len(self.interaction_history)
        }
    def get_all_contacts(self):
        return self.list_contacts()

    def list_contacts(self, **kwargs):
        return self.search_contacts(**kwargs)


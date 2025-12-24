import logging
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import uuid

logger = logging.getLogger(__name__)

class EventTracker:
    def __init__(self, config: dict):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.storage_path = config.get('storage_path', 'data/events.json')
        
        self.events = {}
        self.registrations = {}
        
        if self.enabled:
            self._load_data()
        
        logger.info("EventTracker initialized")
    
    def _load_data(self):
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.events = data.get('events', {})
                    self.registrations = data.get('registrations', {})
                logger.info(f"Loaded {len(self.events)} events")
        except Exception as e:
            logger.error(f"Error loading event data: {e}")
    
    def _save_data(self):
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump({
                    'events': self.events,
                    'registrations': self.registrations,
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving event data: {e}")
    
    def add_event(self, name: str, date: str, time: str = None,
                 event_type: str = None, location: str = None, 
                 url: str = None, organizer: str = None,
                 description: str = "", cost: float = None,
                 duration: int = None) -> Optional[str]:
        if not self.enabled:
            return None
        
        try:
            event_id = str(uuid.uuid4())[:8]
            
            self.events[event_id] = {
                'id': event_id,
                'name': name,
                'date': date,
                'time': time,
                'type': event_type,
                'location': location,
                'url': url,
                'organizer': organizer,
                'description': description,
                'cost': cost,
                'duration': duration,
                'status': 'scheduled',
                'registered': False,
                'attended': False,
                'notes': "",
                'tags': [],
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            self._save_data()
            logger.info(f"Added event: {name}")
            return self.events[event_id].copy()
            
        except Exception as e:
            logger.error(f"Error adding event: {e}")
            return None
    
    def update_event(self, event_id: str, **updates) -> bool:
        if not self.enabled or event_id not in self.events:
            return False
        
        try:
            for key, value in updates.items():
                if key in self.events[event_id]:
                    self.events[event_id][key] = value
            
            self.events[event_id]['updated_at'] = datetime.now().isoformat()
            self._save_data()
            logger.info(f"Updated event: {event_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating event: {e}")
            return False
    
    def register_for_event(self, event_id: str, confirmation: str = None,
                          registration_date: str = None) -> Optional[str]:
        if not self.enabled or event_id not in self.events:
            return None
        
        try:
            reg_id = str(uuid.uuid4())[:8]
            reg_date = registration_date or datetime.now().isoformat()
            
            self.registrations[reg_id] = {
                'id': reg_id,
                'event_id': event_id,
                'event_name': self.events[event_id]['name'],
                'confirmation': confirmation,
                'registration_date': reg_date,
                'status': 'confirmed'
            }
            
            self.events[event_id]['registered'] = True
            self.events[event_id]['updated_at'] = datetime.now().isoformat()
            
            self._save_data()
            logger.info(f"Registered for event: {event_id}")
            return reg_id
            
        except Exception as e:
            logger.error(f"Error registering for event: {e}")
            return None
    
    def mark_attended(self, event_id: str, notes: str = "") -> bool:
        if not self.enabled or event_id not in self.events:
            return False
        
        try:
            self.events[event_id]['attended'] = True
            self.events[event_id]['status'] = 'completed'
            if notes:
                self.events[event_id]['notes'] = notes
            self.events[event_id]['updated_at'] = datetime.now().isoformat()
            self._save_data()
            logger.info(f"Marked event as attended: {event_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error marking event attended: {e}")
            return False
    
    def cancel_event(self, event_id: str) -> bool:
        if not self.enabled or event_id not in self.events:
            return False
        
        try:
            self.events[event_id]['status'] = 'cancelled'
            self.events[event_id]['updated_at'] = datetime.now().isoformat()
            self._save_data()
            logger.info(f"Cancelled event: {event_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling event: {e}")
            return False
    
    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        return self.events.get(event_id)
    
    def list_events(self, event_type: str = None, status: str = None) -> List[Dict[str, Any]]:
        events = list(self.events.values())
        
        if event_type:
            events = [e for e in events if e.get('type') == event_type]
        if status:
            events = [e for e in events if e.get('status') == status]
        
        return sorted(events, key=lambda x: (x.get('date', ''), x.get('time', '')))
    
    def get_upcoming_events(self, days: int = 30) -> List[Dict[str, Any]]:
        upcoming = []
        now = datetime.now()
        cutoff = now + timedelta(days=days)
        
        for event in self.events.values():
            if event['status'] in ['cancelled', 'completed']:
                continue
            
            try:
                event_datetime_str = event['date']
                if event.get('time'):
                    event_datetime_str += 'T' + event['time']
                
                event_datetime = datetime.fromisoformat(event_datetime_str[:16] if 'T' in event_datetime_str else event_datetime_str)
                
                if now <= event_datetime <= cutoff:
                    days_until = (event_datetime.date() - now.date()).days
                    event_copy = event.copy()
                    event_copy['days_until'] = days_until
                    upcoming.append(event_copy)
            except:
                pass
        
        return sorted(upcoming, key=lambda x: (x.get('date', ''), x.get('time', '')))
    
    def get_past_events(self, days: int = 90) -> List[Dict[str, Any]]:
        past = []
        now = datetime.now()
        cutoff = now - timedelta(days=days)
        
        for event in self.events.values():
            try:
                event_date = datetime.fromisoformat(event['date'])
                if cutoff <= event_date < now:
                    past.append(event)
            except:
                pass
        
        return sorted(past, key=lambda x: x.get('date', ''), reverse=True)
    
    def search_events(self, query: str) -> List[Dict[str, Any]]:
        query_lower = query.lower()
        results = []
        
        for event in self.events.values():
            if (query_lower in event['name'].lower() or
                query_lower in event.get('description', '').lower() or
                query_lower in event.get('organizer', '').lower() or
                query_lower in event.get('location', '').lower()):
                results.append(event)
        
        return results
    
    def get_events_by_type(self, event_type: str) -> List[Dict[str, Any]]:
        return [e for e in self.events.values() if e.get('type') == event_type]
    
    def get_registered_events(self) -> List[Dict[str, Any]]:
        return [e for e in self.events.values() if e.get('registered', False)]
    
    def get_stats(self) -> Dict[str, Any]:
        total_events = len(self.events)
        
        by_status = defaultdict(int)
        by_type = defaultdict(int)
        
        for event in self.events.values():
            by_status[event.get('status', 'unknown')] += 1
            if event.get('type'):
                by_type[event['type']] += 1
        
        upcoming = len(self.get_upcoming_events(30))
        registered = sum(1 for e in self.events.values() if e.get('registered', False))
        attended = sum(1 for e in self.events.values() if e.get('attended', False))
        
        total_cost = sum(e.get('cost', 0) or 0 for e in self.events.values() if e.get('registered', False))
        
        return {
            'total_events': total_events,
            'upcoming_events': upcoming,
            'registered_events': registered,
            'attended_events': attended,
            'total_registrations': len(self.registrations),
            'by_status': dict(by_status),
            'by_type': dict(by_type),
            'total_cost': round(total_cost, 2)
        }
    def get_all_events(self):
        return self.list_events()

    
    
    def delete_event(self, event_id: str) -> bool:
        if not self.enabled or event_id not in self.events:
            return False
        del self.events[event_id]
        self._save_data()
        return True

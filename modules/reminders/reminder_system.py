import logging
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import uuid

logger = logging.getLogger(__name__)

class ReminderSystem:
    def __init__(self, config: dict):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.storage_path = config.get('storage_path', 'data/reminders.json')
        
        self.reminders = {}
        self.recurring_templates = {}
        
        if self.enabled:
            self._load_data()
        
        logger.info("ReminderSystem initialized")
    
    def _load_data(self):
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.reminders = data.get('reminders', {})
                    self.recurring_templates = data.get('recurring_templates', {})
                logger.info(f"Loaded {len(self.reminders)} reminders")
        except Exception as e:
            logger.error(f"Error loading reminder data: {e}")
    
    def _save_data(self):
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump({
                    'reminders': self.reminders,
                    'recurring_templates': self.recurring_templates,
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving reminder data: {e}")
    
    def add_reminder(self, title: str, due_date: str, due_time: str = None,
                    description: str = "", priority: str = "medium",
                    category: str = None, tags: List[str] = None) -> Optional[str]:
        if not self.enabled:
            return None
        
        try:
            reminder_id = str(uuid.uuid4())[:8]
            
            self.reminders[reminder_id] = {
                'id': reminder_id,
                'title': title,
                'description': description,
                'due_date': due_date,
                'due_time': due_time,
                'priority': priority,
                'category': category,
                'tags': tags or [],
                'status': 'pending',
                'recurring': False,
                'completed': False,
                'completed_at': None,
                'snoozed_until': None,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            self._save_data()
            logger.info(f"Added reminder: {title}")
            return self.reminders[reminder_id].copy()
            
        except Exception as e:
            logger.error(f"Error adding reminder: {e}")
            return None
    
    def add_recurring_reminder(self, title: str, frequency: str, start_date: str,
                              time: str = None, description: str = "",
                              end_date: str = None, days_of_week: List[str] = None) -> Optional[str]:
        if not self.enabled:
            return None
        
        try:
            template_id = str(uuid.uuid4())[:8]
            
            self.recurring_templates[template_id] = {
                'id': template_id,
                'title': title,
                'description': description,
                'frequency': frequency,
                'start_date': start_date,
                'end_date': end_date,
                'time': time,
                'days_of_week': days_of_week or [],
                'active': True,
                'last_created': None,
                'created_at': datetime.now().isoformat()
            }
            
            self._save_data()
            logger.info(f"Added recurring reminder: {title} ({frequency})")
            return template_id
            
        except Exception as e:
            logger.error(f"Error adding recurring reminder: {e}")
            return None
    
    def complete_reminder(self, reminder_id: str) -> bool:
        if not self.enabled or reminder_id not in self.reminders:
            return False
        
        try:
            self.reminders[reminder_id]['completed'] = True
            self.reminders[reminder_id]['status'] = 'completed'
            self.reminders[reminder_id]['completed_at'] = datetime.now().isoformat()
            self.reminders[reminder_id]['updated_at'] = datetime.now().isoformat()
            self._save_data()
            logger.info(f"Completed reminder: {reminder_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error completing reminder: {e}")
            return False
    
    def snooze_reminder(self, reminder_id: str, minutes: int = 15) -> bool:
        if not self.enabled or reminder_id not in self.reminders:
            return False
        
        try:
            snooze_until = (datetime.now() + timedelta(minutes=minutes)).isoformat()
            self.reminders[reminder_id]['snoozed_until'] = snooze_until
            self.reminders[reminder_id]['updated_at'] = datetime.now().isoformat()
            self._save_data()
            logger.info(f"Snoozed reminder {reminder_id} for {minutes} minutes")
            return True
            
        except Exception as e:
            logger.error(f"Error snoozing reminder: {e}")
            return False
    
    def delete_reminder(self, reminder_id: str) -> bool:
        if not self.enabled or reminder_id not in self.reminders:
            return False
        
        try:
            del self.reminders[reminder_id]
            self._save_data()
            logger.info(f"Deleted reminder: {reminder_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting reminder: {e}")
            return False
    
    def get_reminder(self, reminder_id: str) -> Optional[Dict[str, Any]]:
        return self.reminders.get(reminder_id)
    
    def list_reminders(self, status: str = None, category: str = None) -> List[Dict[str, Any]]:
        reminders = list(self.reminders.values())
        
        if status:
            reminders = [r for r in reminders if r['status'] == status]
        if category:
            reminders = [r for r in reminders if r.get('category') == category]
        
        return sorted(reminders, key=lambda x: (x.get('due_date', ''), x.get('due_time', '')))
    
    def get_due_reminders(self, hours: int = 24) -> List[Dict[str, Any]]:
        due_reminders = []
        now = datetime.now()
        cutoff = now + timedelta(hours=hours)
        
        for reminder in self.reminders.values():
            if reminder['completed']:
                continue
            
            if reminder.get('snoozed_until'):
                snooze_time = datetime.fromisoformat(reminder['snoozed_until'])
                if snooze_time > now:
                    continue
            
            due_datetime_str = reminder['due_date']
            if reminder.get('due_time'):
                due_datetime_str += 'T' + reminder['due_time']
            
            try:
                due_datetime = datetime.fromisoformat(due_datetime_str)
                if due_datetime <= cutoff:
                    due_reminders.append(reminder)
            except:
                pass
        
        return sorted(due_reminders, key=lambda x: (x.get('due_date', ''), x.get('due_time', '')))
    
    def get_overdue_reminders(self) -> List[Dict[str, Any]]:
        overdue = []
        now = datetime.now()
        
        for reminder in self.reminders.values():
            if reminder['completed']:
                continue
            
            due_datetime_str = reminder['due_date']
            if reminder.get('due_time'):
                due_datetime_str += 'T' + reminder['due_time']
            
            try:
                due_datetime = datetime.fromisoformat(due_datetime_str)
                if due_datetime < now:
                    overdue.append(reminder)
            except:
                pass
        
        return sorted(overdue, key=lambda x: (x.get('due_date', ''), x.get('due_time', '')))
    
    def search_reminders(self, query: str) -> List[Dict[str, Any]]:
        query_lower = query.lower()
        results = []
        
        for reminder in self.reminders.values():
            if (query_lower in reminder['title'].lower() or
                query_lower in reminder.get('description', '').lower() or
                query_lower in ' '.join(reminder.get('tags', [])).lower()):
                results.append(reminder)
        
        return results
    
    def get_reminders_by_priority(self, priority: str) -> List[Dict[str, Any]]:
        return [r for r in self.reminders.values() if r.get('priority') == priority and not r['completed']]
    
    def update_reminder(self, reminder_id: str, **updates) -> bool:
        if not self.enabled or reminder_id not in self.reminders:
            return False
        
        try:
            for key, value in updates.items():
                if key in self.reminders[reminder_id]:
                    self.reminders[reminder_id][key] = value
            
            self.reminders[reminder_id]['updated_at'] = datetime.now().isoformat()
            self._save_data()
            logger.info(f"Updated reminder: {reminder_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating reminder: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        total_reminders = len(self.reminders)
        completed = sum(1 for r in self.reminders.values() if r['completed'])
        pending = sum(1 for r in self.reminders.values() if not r['completed'])
        
        overdue = len(self.get_overdue_reminders())
        due_today = len(self.get_due_reminders(24))
        
        by_priority = defaultdict(int)
        by_category = defaultdict(int)
        
        for reminder in self.reminders.values():
            if not reminder['completed']:
                by_priority[reminder.get('priority', 'medium')] += 1
                if reminder.get('category'):
                    by_category[reminder['category']] += 1
        
        return {
            'total_reminders': total_reminders,
            'completed': completed,
            'pending': pending,
            'overdue': overdue,
            'due_today': due_today,
            'by_priority': dict(by_priority),
            'by_category': dict(by_category),
            'recurring_templates': len(self.recurring_templates)
        }
    def get_all_reminders(self):
        return self.list_reminders()

    
    

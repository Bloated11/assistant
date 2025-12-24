import logging
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import uuid

logger = logging.getLogger(__name__)

class TimeTracker:
    def __init__(self, config: dict):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.storage_path = config.get('storage_path', 'data/time_tracking.json')
        
        self.time_entries = {}
        self.projects = {}
        self.active_timer = None
        
        if self.enabled:
            self._load_data()
        
        logger.info("TimeTracker initialized")
    
    def _load_data(self):
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.time_entries = data.get('time_entries', {})
                    self.projects = data.get('projects', {})
                    self.active_timer = data.get('active_timer')
                logger.info(f"Loaded {len(self.time_entries)} time entries")
        except Exception as e:
            logger.error(f"Error loading time tracking data: {e}")
    
    def _save_data(self):
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump({
                    'time_entries': self.time_entries,
                    'projects': self.projects,
                    'active_timer': self.active_timer,
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving time tracking data: {e}")
    
    def start_timer(self, task: str, project: str = None, tags: List[str] = None) -> Optional[str]:
        if not self.enabled:
            return None
        
        try:
            if self.active_timer:
                logger.warning("Timer already running, stopping previous timer")
                self.stop_timer()
            
            entry_id = str(uuid.uuid4())[:8]
            
            self.active_timer = {
                'id': entry_id,
                'task': task,
                'project': project,
                'tags': tags or [],
                'start_time': datetime.now().isoformat(),
                'end_time': None
            }
            
            self._save_data()
            logger.info(f"Started timer for: {task}")
            return entry_id
            
        except Exception as e:
            logger.error(f"Error starting timer: {e}")
            return None
    
    def stop_timer(self) -> Optional[Dict[str, Any]]:
        if not self.enabled or not self.active_timer:
            return None
        
        try:
            self.active_timer['end_time'] = datetime.now().isoformat()
            
            start = datetime.fromisoformat(self.active_timer['start_time'])
            end = datetime.fromisoformat(self.active_timer['end_time'])
            duration = int((end - start).total_seconds() / 60)
            
            self.active_timer['duration'] = duration
            
            entry_id = self.active_timer['id']
            self.time_entries[entry_id] = self.active_timer.copy()
            
            result = self.active_timer.copy()
            self.active_timer = None
            
            self._save_data()
            logger.info(f"Stopped timer: {duration} minutes")
            return result
            
        except Exception as e:
            logger.error(f"Error stopping timer: {e}")
            return None
    
    def log_time(self, task: str, duration: int, project: str = None, 
                tags: List[str] = None, date: str = None) -> Optional[str]:
        if not self.enabled:
            return None
        
        try:
            entry_id = str(uuid.uuid4())[:8]
            entry_date = date or datetime.now().isoformat()
            
            self.time_entries[entry_id] = {
                'id': entry_id,
                'task': task,
                'project': project,
                'tags': tags or [],
                'duration': duration,
                'start_time': entry_date,
                'end_time': entry_date,
                'manual': True
            }
            
            self._save_data()
            logger.info(f"Logged time: {task} - {duration} minutes")
            return entry_id
            
        except Exception as e:
            logger.error(f"Error logging time: {e}")
            return None
    
    def add_project(self, name: str, hourly_rate: float = None, 
                   budget_hours: float = None, client: str = None) -> Optional[str]:
        if not self.enabled:
            return None
        
        try:
            project_id = str(uuid.uuid4())[:8]
            
            self.projects[project_id] = {
                'id': project_id,
                'name': name,
                'hourly_rate': hourly_rate,
                'budget_hours': budget_hours,
                'client': client,
                'created_at': datetime.now().isoformat(),
                'active': True
            }
            
            self._save_data()
            logger.info(f"Added project: {name}")
            return project_id
            
        except Exception as e:
            logger.error(f"Error adding project: {e}")
            return None
    
    def get_active_timer(self) -> Optional[Dict[str, Any]]:
        if not self.enabled or not self.active_timer:
            return None
        
        timer = self.active_timer.copy()
        start = datetime.fromisoformat(timer['start_time'])
        elapsed = int((datetime.now() - start).total_seconds() / 60)
        timer['elapsed'] = elapsed
        
        return timer
    
    def get_time_summary(self, days: int = 7, project: str = None) -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None
        
        try:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            entries = [e for e in self.time_entries.values() 
                      if e['start_time'] >= cutoff]
            
            if project:
                entries = [e for e in entries if e.get('project') == project]
            
            total_time = sum(e['duration'] for e in entries)
            
            project_breakdown = defaultdict(int)
            for e in entries:
                if e.get('project'):
                    project_breakdown[e['project']] += e['duration']
            
            tag_breakdown = defaultdict(int)
            for e in entries:
                for tag in e.get('tags', []):
                    tag_breakdown[tag] += e['duration']
            
            daily_totals = defaultdict(int)
            for e in entries:
                date = e['start_time'][:10]
                daily_totals[date] += e['duration']
            
            return {
                'period_days': days,
                'total_entries': len(entries),
                'total_time': total_time,
                'avg_per_day': total_time / days if days > 0 else 0,
                'project_breakdown': dict(project_breakdown),
                'tag_breakdown': dict(tag_breakdown),
                'daily_totals': dict(sorted(daily_totals.items()))
            }
            
        except Exception as e:
            logger.error(f"Error getting time summary: {e}")
            return None
    
    def get_project_summary(self, project_name: str) -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None
        
        try:
            entries = [e for e in self.time_entries.values() 
                      if e.get('project') == project_name]
            
            total_hours = sum(e['duration'] for e in entries) / 60
            
            project = next((p for p in self.projects.values() 
                          if p['name'] == project_name), None)
            
            summary = {
                'project': project_name,
                'total_entries': len(entries),
                'total_hours': total_hours,
                'total_time': sum(e['duration'] for e in entries)
            }
            
            if project:
                if project.get('hourly_rate'):
                    summary['total_revenue'] = total_hours * project['hourly_rate']
                    summary['hourly_rate'] = project['hourly_rate']
                
                if project.get('budget_hours'):
                    summary['budget_hours'] = project['budget_hours']
                    summary['hours_remaining'] = project['budget_hours'] - total_hours
                    summary['budget_percentage'] = (total_hours / project['budget_hours']) * 100
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting project summary: {e}")
            return None
    
    def get_entries(self, limit: int = 20, project: str = None, 
                   tag: str = None) -> List[Dict[str, Any]]:
        if not self.enabled:
            return []
        
        try:
            entries = list(self.time_entries.values())
            
            if project:
                entries = [e for e in entries if e.get('project') == project]
            
            if tag:
                entries = [e for e in entries if tag in e.get('tags', [])]
            
            entries.sort(key=lambda x: x['start_time'], reverse=True)
            
            return entries[:limit]
            
        except Exception as e:
            logger.error(f"Error getting entries: {e}")
            return []
    
    def delete_entry(self, entry_id: str) -> bool:
        if not self.enabled or entry_id not in self.time_entries:
            return False
        
        try:
            del self.time_entries[entry_id]
            self._save_data()
            logger.info(f"Deleted time entry: {entry_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting entry: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            'enabled': self.enabled,
            'total_entries': len(self.time_entries),
            'total_projects': len(self.projects),
            'active_timer': self.active_timer is not None,
            'total_time_tracked': sum(e.get('duration', 0) for e in self.time_entries.values())
        }
    def start_tracking(self, task: str):
        return self.start_session(task)
    
    def stop_tracking(self):
        return self.stop_session()

    def start_session(self, task: str):
        return self.start_timer(task)

    def stop_session(self) -> bool:
        result = self.stop_timer()
        return result is not None


import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)

class TaskManager:
    def __init__(self, config: dict):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.storage_path = config.get('storage', 'data/tasks.json')
        self.tasks = []
        
        if self.enabled:
            self._load_tasks()
        
        logger.info(f"TaskManager initialized with {len(self.tasks)} tasks")
    
    def _load_tasks(self):
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    content = f.read().strip()
                    if content:
                        self.tasks = json.loads(content)
                        logger.info(f"Loaded {len(self.tasks)} tasks from storage")
                    else:
                        self.tasks = []
            else:
                self.tasks = []
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in tasks file: {e}. Starting with empty task list.")
            self.tasks = []
        except Exception as e:
            logger.error(f"Error loading tasks: {e}")
            self.tasks = []
    
    def _save_tasks(self):
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump(self.tasks, f, indent=2)
            logger.debug("Tasks saved to storage")
        except Exception as e:
            logger.error(f"Error saving tasks: {e}")
    
    def add_task(self, title: str, description: str = "", priority: str = "medium", 
                 due_date: str = None, tags: List[str] = None) -> Dict[str, Any]:
        if not title or not title.strip():
            raise ValueError("Task title cannot be empty")
        
        valid_priorities = ['low', 'medium', 'high', 'urgent']
        if priority not in valid_priorities:
            logger.warning(f"Invalid priority '{priority}', defaulting to 'medium'")
            priority = 'medium'
        
        task_id = max([t['id'] for t in self.tasks], default=0) + 1
        
        task = {
            'id': task_id,
            'title': title.strip(),
            'description': description,
            'priority': priority,
            'status': 'pending',
            'due_date': due_date,
            'tags': tags or [],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'completed_at': None
        }
        
        self.tasks.append(task)
        self._save_tasks()
        
        logger.info(f"Added task: {title}")
        return task
    
    def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        for task in self.tasks:
            if task['id'] == task_id:
                return task
        return None
    
    def update_task(self, task_id: int, **kwargs) -> bool:
        task = self.get_task(task_id)
        if task:
            for key, value in kwargs.items():
                if key in task:
                    task[key] = value
            task['updated_at'] = datetime.now().isoformat()
            self._save_tasks()
            logger.info(f"Updated task {task_id}")
            return True
        return False
    
    def complete_task(self, task_id: int) -> bool:
        task = self.get_task(task_id)
        if task:
            task['status'] = 'completed'
            task['completed_at'] = datetime.now().isoformat()
            task['updated_at'] = datetime.now().isoformat()
            self._save_tasks()
            logger.info(f"Completed task {task_id}")
            return True
        return False
    
    def delete_task(self, task_id: int) -> bool:
        task = self.get_task(task_id)
        if task:
            self.tasks.remove(task)
            self._save_tasks()
            logger.info(f"Deleted task {task_id}")
            return True
        return False
    
    def list_tasks(self, status: str = None, priority: str = None, 
                   tags: List[str] = None) -> List[Dict[str, Any]]:
        filtered_tasks = self.tasks
        
        if status:
            filtered_tasks = [t for t in filtered_tasks if t['status'] == status]
        
        if priority:
            filtered_tasks = [t for t in filtered_tasks if t['priority'] == priority]
        
        if tags:
            filtered_tasks = [t for t in filtered_tasks 
                            if any(tag in t['tags'] for tag in tags)]
        
        return filtered_tasks
    
    def get_pending_tasks(self) -> List[Dict[str, Any]]:
        return self.list_tasks(status='pending')
    
    def get_overdue_tasks(self) -> List[Dict[str, Any]]:
        overdue = []
        now = datetime.now()
        
        for task in self.tasks:
            if task['status'] == 'pending' and task['due_date']:
                try:
                    due_date = datetime.fromisoformat(task['due_date'])
                    if due_date < now:
                        overdue.append(task)
                except:
                    pass
        
        return overdue
    
    def search_tasks(self, query: str) -> List[Dict[str, Any]]:
        query_lower = query.lower()
        return [t for t in self.tasks 
                if query_lower in t['title'].lower() or 
                   query_lower in t['description'].lower()]
    
    def get_task_summary(self) -> Dict[str, int]:
        total = len(self.tasks)
        pending = len([t for t in self.tasks if t['status'] == 'pending'])
        completed = len([t for t in self.tasks if t['status'] == 'completed'])
        overdue = len(self.get_overdue_tasks())
        
        return {
            'total': total,
            'pending': pending,
            'completed': completed,
            'overdue': overdue
        }
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        return self.list_tasks()

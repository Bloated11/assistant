import logging
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Status(Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ProjectManager:
    def __init__(self, config: dict):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.storage_path = config.get('storage_path', 'data/projects.json')
        
        self.projects = {}
        self.active_project = None
        
        if self.enabled:
            self._load_projects()
        
        logger.info("ProjectManager initialized")
    
    def _load_projects(self):
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.projects = data.get('projects', {})
                    self.active_project = data.get('active_project')
                logger.info(f"Loaded {len(self.projects)} projects")
        except Exception as e:
            logger.error(f"Error loading projects: {e}")
    
    def _save_projects(self):
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump({
                    'projects': self.projects,
                    'active_project': self.active_project,
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving projects: {e}")
    
    def create_project(self, name: str, description: str = "", deadline: str = None, team: List[str] = None) -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None
        
        try:
            project_id = self._generate_project_id(name)
            
            if project_id in self.projects:
                logger.warning(f"Project '{name}' already exists")
                return None
            
            self.projects[project_id] = {
                'id': project_id,
                'name': name,
                'description': description,
                'status': Status.PLANNED.value,
                'priority': Priority.MEDIUM.value,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'deadline': deadline,
                'team': team or [],
                'tasks': {},
                'milestones': {},
                'resources': {},
                'notes': [],
                'tags': [],
                'completion_percentage': 0
            }
            
            self._save_projects()
            logger.info(f"Created project: {name}")
            return self.projects[project_id]
            
        except Exception as e:
            logger.error(f"Error creating project: {e}")
            return None
    
    def add_task(self, project_name: str, task_name: str, description: str = "", 
                 priority: str = "medium", assignee: str = None, deadline: str = None,
                 dependencies: List[str] = None) -> bool:
        if not self.enabled:
            return False
        
        try:
            project_id = self._find_project_id(project_name)
            if not project_id:
                logger.warning(f"Project '{project_name}' not found")
                return False
            
            task_id = self._generate_task_id(task_name)
            project = self.projects[project_id]
            
            if task_id in project['tasks']:
                logger.warning(f"Task '{task_name}' already exists in project")
                return False
            
            project['tasks'][task_id] = {
                'id': task_id,
                'name': task_name,
                'description': description,
                'status': Status.PLANNED.value,
                'priority': priority,
                'assignee': assignee,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'deadline': deadline,
                'dependencies': dependencies or [],
                'subtasks': [],
                'time_spent': 0,
                'estimated_hours': None,
                'completion_percentage': 0
            }
            
            project['updated_at'] = datetime.now().isoformat()
            self._update_project_progress(project_id)
            self._save_projects()
            
            logger.info(f"Added task '{task_name}' to project '{project_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Error adding task: {e}")
            return False
    
    def update_task_status(self, project_name: str, task_name: str, status: str) -> bool:
        if not self.enabled:
            return False
        
        try:
            project_id = self._find_project_id(project_name)
            if not project_id:
                return False
            
            project = self.projects[project_id]
            task_id = self._find_task_id(project, task_name)
            
            if not task_id:
                logger.warning(f"Task '{task_name}' not found")
                return False
            
            task = project['tasks'][task_id]
            task['status'] = status
            task['updated_at'] = datetime.now().isoformat()
            
            if status == Status.COMPLETED.value:
                task['completed_at'] = datetime.now().isoformat()
                task['completion_percentage'] = 100
            
            project['updated_at'] = datetime.now().isoformat()
            self._update_project_progress(project_id)
            self._save_projects()
            
            logger.info(f"Updated task '{task_name}' status to '{status}'")
            return True
            
        except Exception as e:
            logger.error(f"Error updating task status: {e}")
            return False
    
    def add_milestone(self, project_name: str, milestone_name: str, description: str = "", 
                     target_date: str = None, criteria: List[str] = None) -> bool:
        if not self.enabled:
            return False
        
        try:
            project_id = self._find_project_id(project_name)
            if not project_id:
                return False
            
            milestone_id = self._generate_milestone_id(milestone_name)
            project = self.projects[project_id]
            
            project['milestones'][milestone_id] = {
                'id': milestone_id,
                'name': milestone_name,
                'description': description,
                'target_date': target_date,
                'completion_criteria': criteria or [],
                'status': Status.PLANNED.value,
                'created_at': datetime.now().isoformat(),
                'completed_at': None
            }
            
            project['updated_at'] = datetime.now().isoformat()
            self._save_projects()
            
            logger.info(f"Added milestone '{milestone_name}' to project '{project_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Error adding milestone: {e}")
            return False
    
    def set_active_project(self, project_name: str) -> bool:
        if not self.enabled:
            return False
        
        project_id = self._find_project_id(project_name)
        if project_id:
            self.active_project = project_id
            self._save_projects()
            logger.info(f"Set active project to '{project_name}'")
            return True
        return False
    
    def get_project_summary(self, project_name: str) -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None
        
        project_id = self._find_project_id(project_name)
        if not project_id:
            return None
        
        project = self.projects[project_id]
        
        total_tasks = len(project['tasks'])
        completed_tasks = sum(1 for task in project['tasks'].values() 
                             if task['status'] == Status.COMPLETED.value)
        in_progress_tasks = sum(1 for task in project['tasks'].values() 
                               if task['status'] == Status.IN_PROGRESS.value)
        
        total_milestones = len(project['milestones'])
        completed_milestones = sum(1 for ms in project['milestones'].values() 
                                  if ms['status'] == Status.COMPLETED.value)
        
        overdue_tasks = []
        if project.get('deadline'):
            try:
                deadline = datetime.fromisoformat(project['deadline'])
                if datetime.now() > deadline and project['status'] != Status.COMPLETED.value:
                    overdue_tasks.append(f"Project deadline: {project['deadline']}")
            except:
                pass
        
        return {
            'name': project['name'],
            'description': project['description'],
            'status': project['status'],
            'priority': project['priority'],
            'completion_percentage': project['completion_percentage'],
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'in_progress_tasks': in_progress_tasks,
            'total_milestones': total_milestones,
            'completed_milestones': completed_milestones,
            'team_size': len(project['team']),
            'deadline': project.get('deadline'),
            'overdue': len(overdue_tasks) > 0,
            'created_at': project['created_at'],
            'updated_at': project['updated_at']
        }
    
    def list_projects(self, filter_status: str = None) -> List[Dict[str, Any]]:
        if not self.enabled:
            return []
        
        projects = []
        for project_id, project in self.projects.items():
            if filter_status and project['status'] != filter_status:
                continue
            
            projects.append({
                'id': project_id,
                'name': project['name'],
                'status': project['status'],
                'priority': project['priority'],
                'completion_percentage': project['completion_percentage'],
                'tasks': len(project['tasks']),
                'deadline': project.get('deadline'),
                'is_active': project_id == self.active_project
            })
        
        return sorted(projects, key=lambda x: x['priority'], reverse=True)
    
    def get_task_details(self, project_name: str, task_name: str) -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None
        
        project_id = self._find_project_id(project_name)
        if not project_id:
            return None
        
        project = self.projects[project_id]
        task_id = self._find_task_id(project, task_name)
        
        if not task_id:
            return None
        
        return project['tasks'][task_id]
    
    def add_team_member(self, project_name: str, member_name: str, role: str = None) -> bool:
        if not self.enabled:
            return False
        
        try:
            project_id = self._find_project_id(project_name)
            if not project_id:
                return False
            
            project = self.projects[project_id]
            
            member = {
                'name': member_name,
                'role': role,
                'joined_at': datetime.now().isoformat()
            }
            
            if member not in project['team']:
                project['team'].append(member)
                project['updated_at'] = datetime.now().isoformat()
                self._save_projects()
                logger.info(f"Added {member_name} to project '{project_name}'")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error adding team member: {e}")
            return False
    
    def get_project_timeline(self, project_name: str) -> Optional[List[Dict[str, Any]]]:
        if not self.enabled:
            return None
        
        project_id = self._find_project_id(project_name)
        if not project_id:
            return None
        
        project = self.projects[project_id]
        timeline = []
        
        timeline.append({
            'date': project['created_at'],
            'event': 'Project Created',
            'type': 'project'
        })
        
        for task in project['tasks'].values():
            timeline.append({
                'date': task['created_at'],
                'event': f"Task Created: {task['name']}",
                'type': 'task'
            })
            if task.get('completed_at'):
                timeline.append({
                    'date': task['completed_at'],
                    'event': f"Task Completed: {task['name']}",
                    'type': 'task'
                })
        
        for milestone in project['milestones'].values():
            timeline.append({
                'date': milestone['created_at'],
                'event': f"Milestone Set: {milestone['name']}",
                'type': 'milestone'
            })
            if milestone.get('completed_at'):
                timeline.append({
                    'date': milestone['completed_at'],
                    'event': f"Milestone Reached: {milestone['name']}",
                    'type': 'milestone'
                })
        
        timeline.sort(key=lambda x: x['date'], reverse=True)
        return timeline
    
    def _update_project_progress(self, project_id: str):
        project = self.projects[project_id]
        
        if not project['tasks']:
            project['completion_percentage'] = 0
            return
        
        total_tasks = len(project['tasks'])
        completed_tasks = sum(1 for task in project['tasks'].values() 
                             if task['status'] == Status.COMPLETED.value)
        
        project['completion_percentage'] = int((completed_tasks / total_tasks) * 100)
        
        if project['completion_percentage'] == 100:
            project['status'] = Status.COMPLETED.value
        elif completed_tasks > 0:
            project['status'] = Status.IN_PROGRESS.value
    
    def _generate_project_id(self, name: str) -> str:
        return name.lower().replace(' ', '_')
    
    def _generate_task_id(self, name: str) -> str:
        return name.lower().replace(' ', '_')
    
    def _generate_milestone_id(self, name: str) -> str:
        return name.lower().replace(' ', '_')
    
    def _find_project_id(self, name: str) -> Optional[str]:
        name_lower = name.lower()
        for project_id, project in self.projects.items():
            if project['name'].lower() == name_lower or project_id == name_lower:
                return project_id
        return None
    
    def _find_task_id(self, project: dict, task_name: str) -> Optional[str]:
        task_name_lower = task_name.lower()
        for task_id, task in project['tasks'].items():
            if task['name'].lower() == task_name_lower or task_id == task_name_lower:
                return task_id
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        if not self.enabled:
            return {'enabled': False}
        
        total_projects = len(self.projects)
        active_projects = sum(1 for p in self.projects.values() 
                             if p['status'] == Status.IN_PROGRESS.value)
        completed_projects = sum(1 for p in self.projects.values() 
                                if p['status'] == Status.COMPLETED.value)
        
        total_tasks = sum(len(p['tasks']) for p in self.projects.values())
        completed_tasks = sum(
            sum(1 for t in p['tasks'].values() if t['status'] == Status.COMPLETED.value)
            for p in self.projects.values()
        )
        
        return {
            'enabled': True,
            'total_projects': total_projects,
            'active_projects': active_projects,
            'completed_projects': completed_projects,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'active_project': self.projects.get(self.active_project, {}).get('name') if self.active_project else None
        }


    def delete_project(self, project_id: str) -> bool:
        if not self.enabled or project_id not in self.projects:
            return False
        try:
            del self.projects[project_id]
            self._save_projects()
            logger.info(f"Deleted project: {project_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting project: {e}")
            return False

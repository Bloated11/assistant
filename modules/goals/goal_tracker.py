import logging
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import uuid

logger = logging.getLogger(__name__)

class GoalTracker:
    def __init__(self, config: dict):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.storage_path = config.get('storage_path', 'data/goals.json')
        
        self.goals = {}
        self.categories = set(['Personal', 'Career', 'Health', 'Financial', 'Learning', 'Relationship'])
        
        if self.enabled:
            self._load_goals()
        
        logger.info("GoalTracker initialized")
    
    def _load_goals(self):
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.goals = data.get('goals', {})
                    self.categories = set(data.get('categories', list(self.categories)))
                logger.info(f"Loaded {len(self.goals)} goals")
        except Exception as e:
            logger.error(f"Error loading goals: {e}")
    
    def _save_goals(self):
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump({
                    'goals': self.goals,
                    'categories': list(self.categories),
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving goals: {e}")
    
    def create_goal(self, title: str, description: str = "", category: str = None,
                   target_date: str = None, priority: str = "medium", 
                   measurable: bool = False, target_value: float = None) -> Optional[str]:
        if not self.enabled:
            return None
        
        try:
            goal_id = str(uuid.uuid4())[:8]
            
            if category:
                self.categories.add(category)
            
            self.goals[goal_id] = {
                'id': goal_id,
                'title': title,
                'description': description,
                'category': category,
                'priority': priority,
                'status': 'active',
                'progress': 0.0,
                'measurable': measurable,
                'target_value': target_value,
                'current_value': 0.0 if measurable else None,
                'target_date': target_date,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'completed_at': None,
                'milestones': {},
                'sub_goals': {},
                'notes': [],
                'reflections': []
            }
            
            self._save_goals()
            logger.info(f"Created goal: {title}")
            return goal_id
            
        except Exception as e:
            logger.error(f"Error creating goal: {e}")
            return None
    
    def update_progress(self, goal_id: str, progress: float = None, 
                       current_value: float = None, notes: str = None) -> bool:
        if not self.enabled or goal_id not in self.goals:
            return False
        
        try:
            goal = self.goals[goal_id]
            
            if progress is not None:
                goal['progress'] = min(100.0, max(0.0, float(progress)))
            
            if current_value is not None and goal['measurable']:
                goal['current_value'] = float(current_value)
                if goal['target_value']:
                    goal['progress'] = min(100.0, (current_value / goal['target_value']) * 100)
            
            if notes:
                goal['notes'].append({
                    'timestamp': datetime.now().isoformat(),
                    'note': notes
                })
            
            if goal['progress'] >= 100.0:
                goal['status'] = 'completed'
                goal['completed_at'] = datetime.now().isoformat()
            
            goal['updated_at'] = datetime.now().isoformat()
            self._save_goals()
            
            logger.info(f"Updated progress for goal {goal_id}: {goal['progress']}%")
            return self.goals[goal_id].copy()
            
        except Exception as e:
            logger.error(f"Error updating progress: {e}")
            return False
    
    def add_milestone(self, goal_id: str, milestone_title: str, 
                     description: str = "", target_date: str = None) -> bool:
        if not self.enabled or goal_id not in self.goals:
            return False
        
        try:
            milestone_id = str(uuid.uuid4())[:8]
            goal = self.goals[goal_id]
            
            goal['milestones'][milestone_id] = {
                'id': milestone_id,
                'title': milestone_title,
                'description': description,
                'target_date': target_date,
                'completed': False,
                'completed_at': None,
                'created_at': datetime.now().isoformat()
            }
            
            goal['updated_at'] = datetime.now().isoformat()
            self._save_goals()
            
            logger.info(f"Added milestone to goal {goal_id}: {milestone_title}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding milestone: {e}")
            return False
    
    def complete_milestone(self, goal_id: str, milestone_id: str) -> bool:
        if not self.enabled or goal_id not in self.goals:
            return False
        
        goal = self.goals[goal_id]
        if milestone_id not in goal['milestones']:
            return False
        
        milestone = goal['milestones'][milestone_id]
        milestone['completed'] = True
        milestone['completed_at'] = datetime.now().isoformat()
        
        self._update_goal_progress_from_milestones(goal_id)
        self._save_goals()
        
        return True
    
    def _update_goal_progress_from_milestones(self, goal_id: str):
        goal = self.goals[goal_id]
        milestones = goal['milestones']
        
        if not milestones:
            return
        
        completed = sum(1 for m in milestones.values() if m['completed'])
        total = len(milestones)
        
        milestone_progress = (completed / total) * 100 if total > 0 else 0
        
        if not goal['measurable']:
            goal['progress'] = milestone_progress
            
            if milestone_progress >= 100.0:
                goal['status'] = 'completed'
                goal['completed_at'] = datetime.now().isoformat()
    
    def add_sub_goal(self, goal_id: str, sub_goal_title: str, 
                     description: str = "") -> Optional[str]:
        if not self.enabled or goal_id not in self.goals:
            return None
        
        try:
            sub_goal_id = str(uuid.uuid4())[:8]
            goal = self.goals[goal_id]
            
            goal['sub_goals'][sub_goal_id] = {
                'id': sub_goal_id,
                'title': sub_goal_title,
                'description': description,
                'completed': False,
                'completed_at': None,
                'created_at': datetime.now().isoformat()
            }
            
            goal['updated_at'] = datetime.now().isoformat()
            self._save_goals()
            
            logger.info(f"Added sub-goal to goal {goal_id}: {sub_goal_title}")
            return sub_goal_id
            
        except Exception as e:
            logger.error(f"Error adding sub-goal: {e}")
            return None
    
    def complete_sub_goal(self, goal_id: str, sub_goal_id: str) -> bool:
        if not self.enabled or goal_id not in self.goals:
            return False
        
        goal = self.goals[goal_id]
        if sub_goal_id not in goal['sub_goals']:
            return False
        
        sub_goal = goal['sub_goals'][sub_goal_id]
        sub_goal['completed'] = True
        sub_goal['completed_at'] = datetime.now().isoformat()
        
        self._update_goal_progress_from_sub_goals(goal_id)
        self._save_goals()
        
        return True
    
    def _update_goal_progress_from_sub_goals(self, goal_id: str):
        goal = self.goals[goal_id]
        sub_goals = goal['sub_goals']
        
        if not sub_goals:
            return
        
        completed = sum(1 for sg in sub_goals.values() if sg['completed'])
        total = len(sub_goals)
        
        sub_goal_progress = (completed / total) * 100 if total > 0 else 0
        
        if not goal['measurable'] and not goal['milestones']:
            goal['progress'] = sub_goal_progress
            
            if sub_goal_progress >= 100.0:
                goal['status'] = 'completed'
                goal['completed_at'] = datetime.now().isoformat()
    
    def add_reflection(self, goal_id: str, reflection: str) -> bool:
        if not self.enabled or goal_id not in self.goals:
            return False
        
        goal = self.goals[goal_id]
        goal['reflections'].append({
            'timestamp': datetime.now().isoformat(),
            'reflection': reflection
        })
        
        self._save_goals()
        return True
    
    def get_goal(self, goal_id: str) -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None
        
        return self.goals.get(goal_id)
    
    def list_goals(self, status: str = None, category: str = None, 
                  priority: str = None) -> List[Dict[str, Any]]:
        if not self.enabled:
            return []
        
        goals_list = []
        
        for goal_id, goal in self.goals.items():
            if status and goal['status'] != status:
                continue
            
            if category and goal.get('category') != category:
                continue
            
            if priority and goal['priority'] != priority:
                continue
            
            goals_list.append({
                'id': goal['id'],
                'title': goal['title'],
                'category': goal.get('category'),
                'priority': goal['priority'],
                'status': goal['status'],
                'progress': goal['progress'],
                'target_date': goal.get('target_date'),
                'updated_at': goal['updated_at']
            })
        
        goals_list.sort(key=lambda x: (
            0 if x['status'] == 'active' else 1,
            {'high': 0, 'medium': 1, 'low': 2}.get(x['priority'], 1),
            x['updated_at']
        ), reverse=True)
        
        return goals_list
    
    def get_goal_details(self, goal_id: str) -> Optional[Dict[str, Any]]:
        if not self.enabled or goal_id not in self.goals:
            return None
        
        goal = self.goals[goal_id]
        
        milestones_completed = sum(1 for m in goal['milestones'].values() if m['completed'])
        sub_goals_completed = sum(1 for sg in goal['sub_goals'].values() if sg['completed'])
        
        days_active = None
        if goal.get('target_date'):
            try:
                target = datetime.fromisoformat(goal['target_date'])
                days_remaining = (target.date() - datetime.now().date()).days
                days_active = days_remaining
            except:
                pass
        
        return {
            'id': goal['id'],
            'title': goal['title'],
            'description': goal['description'],
            'category': goal.get('category'),
            'priority': goal['priority'],
            'status': goal['status'],
            'progress': goal['progress'],
            'measurable': goal['measurable'],
            'current_value': goal.get('current_value'),
            'target_value': goal.get('target_value'),
            'target_date': goal.get('target_date'),
            'days_remaining': days_active,
            'milestones_total': len(goal['milestones']),
            'milestones_completed': milestones_completed,
            'sub_goals_total': len(goal['sub_goals']),
            'sub_goals_completed': sub_goals_completed,
            'notes_count': len(goal['notes']),
            'reflections_count': len(goal['reflections']),
            'created_at': goal['created_at'],
            'updated_at': goal['updated_at'],
            'completed_at': goal.get('completed_at')
        }
    
    def archive_goal(self, goal_id: str) -> bool:
        if not self.enabled or goal_id not in self.goals:
            return False
        
        self.goals[goal_id]['status'] = 'archived'
        self._save_goals()
        return True
    
    def delete_goal(self, goal_id: str) -> bool:
        if not self.enabled or goal_id not in self.goals:
            return False
        
        del self.goals[goal_id]
        self._save_goals()
        return True
    
    def get_category_summary(self, category: str = None) -> Dict[str, Any]:
        if not self.enabled:
            return {'enabled': False}
        
        if category:
            goals = [g for g in self.goals.values() if g.get('category') == category]
        else:
            goals = list(self.goals.values())
        
        if not goals:
            return {'goals': 0}
        
        total = len(goals)
        active = sum(1 for g in goals if g['status'] == 'active')
        completed = sum(1 for g in goals if g['status'] == 'completed')
        avg_progress = sum(g['progress'] for g in goals) / total if total > 0 else 0
        
        return {
            'category': category or 'All',
            'total_goals': total,
            'active_goals': active,
            'completed_goals': completed,
            'average_progress': round(avg_progress, 1),
            'completion_rate': round((completed / total * 100), 1) if total > 0 else 0
        }
    
    def get_analytics(self) -> Dict[str, Any]:
        if not self.enabled:
            return {'enabled': False}
        
        total_goals = len(self.goals)
        active_goals = sum(1 for g in self.goals.values() if g['status'] == 'active')
        completed_goals = sum(1 for g in self.goals.values() if g['status'] == 'completed')
        
        high_priority = sum(1 for g in self.goals.values() if g['priority'] == 'high')
        
        total_progress = sum(g['progress'] for g in self.goals.values() if g['status'] == 'active')
        avg_progress = total_progress / active_goals if active_goals > 0 else 0
        
        overdue_goals = 0
        for goal in self.goals.values():
            if goal['status'] == 'active' and goal.get('target_date'):
                try:
                    target = datetime.fromisoformat(goal['target_date'])
                    if datetime.now() > target:
                        overdue_goals += 1
                except:
                    pass
        
        category_breakdown = {}
        for goal in self.goals.values():
            cat = goal.get('category', 'Uncategorized')
            if cat not in category_breakdown:
                category_breakdown[cat] = {'total': 0, 'completed': 0}
            category_breakdown[cat]['total'] += 1
            if goal['status'] == 'completed':
                category_breakdown[cat]['completed'] += 1
        
        return {
            'enabled': True,
            'total_goals': total_goals,
            'active_goals': active_goals,
            'completed_goals': completed_goals,
            'high_priority_goals': high_priority,
            'average_progress': round(avg_progress, 1),
            'overdue_goals': overdue_goals,
            'category_breakdown': category_breakdown
        }
    
    def get_stats(self) -> Dict[str, Any]:
        if not self.enabled:
            return {'enabled': False}
        
        return self.get_analytics()

    
    def get_all_goals(self) -> List[Dict[str, Any]]:
        goals_list = []
        for goal_id, goal in self.goals.items():
            goal_copy = goal.copy()
            goal_copy['id'] = goal_id
            goals_list.append(goal_copy)
        return goals_list
    
    def add_goal(self, title: str, description: str = "", target_date: str = None, **kwargs):
        goal_id = self.create_goal(title, description, target_date, **kwargs)
        if goal_id:
            return self.goals[goal_id].copy()
        return None

    def remove_goal(self, goal_id: str) -> bool:
        if not self.enabled or goal_id not in self.goals:
            return False
        try:
            del self.goals[goal_id]
            self._save_goals()
            return True
        except:
            return False

import logging
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)

class HabitTracker:
    def __init__(self, config: dict):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.storage_path = config.get('storage_path', 'data/habits.json')
        self.reminder_enabled = config.get('reminder_enabled', True)
        
        self.habits = {}
        self.completions = defaultdict(list)
        
        if self.enabled:
            self._load_habits()
        
        logger.info("HabitTracker initialized")
    
    def _load_habits(self):
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.habits = data.get('habits', {})
                    self.completions = defaultdict(list, data.get('completions', {}))
                logger.info(f"Loaded {len(self.habits)} habits")
        except Exception as e:
            logger.error(f"Error loading habits: {e}")
    
    def _save_habits(self):
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump({
                    'habits': self.habits,
                    'completions': dict(self.completions),
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving habits: {e}")
    
    def create_habit(self, name: str, description: str = "", frequency: str = "daily", 
                     target_count: int = 1, category: str = None, reminder_time: str = None) -> bool:
        if not self.enabled:
            return False
        
        try:
            habit_id = self._generate_habit_id(name)
            
            if habit_id in self.habits:
                logger.warning(f"Habit '{name}' already exists")
                return False
            
            self.habits[habit_id] = {
                'id': habit_id,
                'name': name,
                'description': description,
                'frequency': frequency,
                'target_count': target_count,
                'category': category,
                'reminder_time': reminder_time,
                'created_at': datetime.now().isoformat(),
                'active': True,
                'current_streak': 0,
                'longest_streak': 0,
                'total_completions': 0
            }
            
            self.completions[habit_id] = []
            self._save_habits()
            
            logger.info(f"Created habit: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating habit: {e}")
            return False
    
    def log_completion(self, habit_name: str, notes: str = None, timestamp: str = None) -> bool:
        if not self.enabled:
            return False
        
        try:
            habit_id = self._find_habit_id(habit_name)
            if not habit_id:
                logger.warning(f"Habit '{habit_name}' not found")
                return False
            
            habit = self.habits[habit_id]
            
            if not habit['active']:
                logger.warning(f"Habit '{habit_name}' is inactive")
                return False
            
            completion_time = timestamp or datetime.now().isoformat()
            
            completion = {
                'timestamp': completion_time,
                'notes': notes,
                'date': completion_time[:10]
            }
            
            self.completions[habit_id].append(completion)
            
            habit['total_completions'] += 1
            self._update_streaks(habit_id)
            self._save_habits()
            
            logger.info(f"Logged completion for habit: {habit_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error logging completion: {e}")
            return False
    
    def _update_streaks(self, habit_id: str):
        habit = self.habits[habit_id]
        completions = self.completions[habit_id]
        
        if not completions:
            habit['current_streak'] = 0
            return
        
        completion_dates = sorted(set(c['date'] for c in completions), reverse=True)
        
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        
        current_streak = 0
        longest_streak = 0
        temp_streak = 0
        
        expected_date = today
        for date_str in completion_dates:
            date = datetime.fromisoformat(date_str).date()
            
            if date == expected_date or date == expected_date - timedelta(days=1):
                temp_streak += 1
                longest_streak = max(longest_streak, temp_streak)
                expected_date = date - timedelta(days=1)
            else:
                if current_streak == 0:
                    current_streak = temp_streak
                temp_streak = 1
                expected_date = date - timedelta(days=1)
        
        if completion_dates:
            latest_date = datetime.fromisoformat(completion_dates[0]).date()
            if latest_date == today or latest_date == yesterday:
                habit['current_streak'] = temp_streak
            else:
                habit['current_streak'] = 0
        
        habit['longest_streak'] = longest_streak
    
    def get_habit_status(self, habit_name: str) -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None
        
        habit_id = self._find_habit_id(habit_name)
        if not habit_id:
            return None
        
        habit = self.habits[habit_id]
        completions = self.completions[habit_id]
        
        today = datetime.now().date().isoformat()
        completed_today = any(c['date'] == today for c in completions)
        
        week_ago = (datetime.now() - timedelta(days=7)).date().isoformat()
        completions_this_week = sum(1 for c in completions if c['date'] >= week_ago)
        
        month_ago = (datetime.now() - timedelta(days=30)).date().isoformat()
        completions_this_month = sum(1 for c in completions if c['date'] >= month_ago)
        
        return {
            'name': habit['name'],
            'description': habit['description'],
            'frequency': habit['frequency'],
            'category': habit.get('category'),
            'active': habit['active'],
            'current_streak': habit['current_streak'],
            'longest_streak': habit['longest_streak'],
            'total_completions': habit['total_completions'],
            'completed_today': completed_today,
            'completions_this_week': completions_this_week,
            'completions_this_month': completions_this_month,
            'created_at': habit['created_at']
        }
    
    def list_habits(self, category: str = None, active_only: bool = True) -> List[Dict[str, Any]]:
        if not self.enabled:
            return []
        
        habits_list = []
        today = datetime.now().date().isoformat()
        
        for habit_id, habit in self.habits.items():
            if active_only and not habit['active']:
                continue
            
            if category and habit.get('category') != category:
                continue
            
            completions = self.completions[habit_id]
            completed_today = any(c['date'] == today for c in completions)
            
            habits_list.append({
                'name': habit['name'],
                'category': habit.get('category'),
                'current_streak': habit['current_streak'],
                'completed_today': completed_today,
                'frequency': habit['frequency']
            })
        
        return sorted(habits_list, key=lambda x: x['current_streak'], reverse=True)
    
    def get_analytics(self, habit_name: str = None, days: int = 30) -> Dict[str, Any]:
        if not self.enabled:
            return {'enabled': False}
        
        if habit_name:
            habit_id = self._find_habit_id(habit_name)
            if not habit_id:
                return {}
            
            return self._get_habit_analytics(habit_id, days)
        else:
            return self._get_overall_analytics(days)
    
    def _get_habit_analytics(self, habit_id: str, days: int) -> Dict[str, Any]:
        habit = self.habits[habit_id]
        completions = self.completions[habit_id]
        
        cutoff_date = (datetime.now() - timedelta(days=days)).date().isoformat()
        recent_completions = [c for c in completions if c['date'] >= cutoff_date]
        
        completion_rate = (len(recent_completions) / days) * 100 if days > 0 else 0
        
        completions_by_date = defaultdict(int)
        for c in recent_completions:
            completions_by_date[c['date']] += 1
        
        best_day = max(completions_by_date.items(), key=lambda x: x[1]) if completions_by_date else (None, 0)
        
        return {
            'habit_name': habit['name'],
            'days_analyzed': days,
            'total_completions': len(recent_completions),
            'completion_rate': round(completion_rate, 1),
            'current_streak': habit['current_streak'],
            'longest_streak': habit['longest_streak'],
            'best_day': best_day[0],
            'best_day_count': best_day[1],
            'average_per_day': round(len(recent_completions) / days, 2) if days > 0 else 0
        }
    
    def _get_overall_analytics(self, days: int) -> Dict[str, Any]:
        total_habits = len([h for h in self.habits.values() if h['active']])
        
        cutoff_date = (datetime.now() - timedelta(days=days)).date().isoformat()
        
        total_completions = 0
        habits_with_streaks = 0
        max_streak = 0
        
        for habit_id, habit in self.habits.items():
            if not habit['active']:
                continue
            
            recent_completions = [c for c in self.completions[habit_id] if c['date'] >= cutoff_date]
            total_completions += len(recent_completions)
            
            if habit['current_streak'] > 0:
                habits_with_streaks += 1
            
            max_streak = max(max_streak, habit['current_streak'])
        
        today = datetime.now().date().isoformat()
        habits_completed_today = sum(
            1 for habit_id in self.habits.keys()
            if any(c['date'] == today for c in self.completions[habit_id])
        )
        
        return {
            'enabled': True,
            'total_active_habits': total_habits,
            'habits_completed_today': habits_completed_today,
            'total_completions_period': total_completions,
            'habits_with_active_streaks': habits_with_streaks,
            'longest_current_streak': max_streak,
            'days_analyzed': days,
            'average_completions_per_day': round(total_completions / days, 1) if days > 0 else 0
        }
    
    def archive_habit(self, habit_name: str) -> bool:
        if not self.enabled:
            return False
        
        habit_id = self._find_habit_id(habit_name)
        if not habit_id:
            return False
        
        self.habits[habit_id]['active'] = False
        self._save_habits()
        logger.info(f"Archived habit: {habit_name}")
        return True
    
    def activate_habit(self, habit_name: str) -> bool:
        if not self.enabled:
            return False
        
        habit_id = self._find_habit_id(habit_name)
        if not habit_id:
            return False
        
        self.habits[habit_id]['active'] = True
        self._save_habits()
        logger.info(f"Activated habit: {habit_name}")
        return True
    
    def delete_habit(self, habit_name: str) -> bool:
        if not self.enabled:
            return False
        
        habit_id = self._find_habit_id(habit_name)
        if not habit_id:
            return False
        
        del self.habits[habit_id]
        if habit_id in self.completions:
            del self.completions[habit_id]
        
        self._save_habits()
        logger.info(f"Deleted habit: {habit_name}")
        return True
    
    def get_today_summary(self) -> Dict[str, Any]:
        if not self.enabled:
            return {'enabled': False}
        
        today = datetime.now().date().isoformat()
        
        active_habits = [h for h in self.habits.values() if h['active']]
        total_habits = len(active_habits)
        
        completed_today = []
        pending_today = []
        
        for habit in active_habits:
            habit_id = habit['id']
            is_completed = any(c['date'] == today for c in self.completions[habit_id])
            
            if is_completed:
                completed_today.append(habit['name'])
            else:
                pending_today.append(habit['name'])
        
        completion_percentage = (len(completed_today) / total_habits * 100) if total_habits > 0 else 0
        
        return {
            'enabled': True,
            'date': today,
            'total_habits': total_habits,
            'completed': len(completed_today),
            'pending': len(pending_today),
            'completion_percentage': round(completion_percentage, 1),
            'completed_habits': completed_today,
            'pending_habits': pending_today
        }
    
    def get_history(self, habit_name: str, days: int = 7) -> List[Dict[str, Any]]:
        if not self.enabled:
            return []
        
        habit_id = self._find_habit_id(habit_name)
        if not habit_id:
            return []
        
        cutoff_date = (datetime.now() - timedelta(days=days)).date().isoformat()
        recent_completions = [
            c for c in self.completions[habit_id]
            if c['date'] >= cutoff_date
        ]
        
        return sorted(recent_completions, key=lambda x: x['timestamp'], reverse=True)
    
    def _generate_habit_id(self, name: str) -> str:
        return name.lower().replace(' ', '_')
    
    def _find_habit_id(self, name: str) -> Optional[str]:
        name_lower = name.lower()
        for habit_id, habit in self.habits.items():
            if habit['name'].lower() == name_lower or habit_id == name_lower:
                return habit_id
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        if not self.enabled:
            return {'enabled': False}
        
        active_habits = sum(1 for h in self.habits.values() if h['active'])
        total_completions = sum(h['total_completions'] for h in self.habits.values())
        
        habits_with_streaks = sum(1 for h in self.habits.values() 
                                 if h['active'] and h['current_streak'] > 0)
        
        avg_streak = sum(h['current_streak'] for h in self.habits.values() if h['active']) / active_habits if active_habits > 0 else 0
        
        return {
            'enabled': True,
            'total_habits': len(self.habits),
            'active_habits': active_habits,
            'total_completions': total_completions,
            'habits_with_active_streaks': habits_with_streaks,
            'average_current_streak': round(avg_streak, 1)
        }
    
    def add_habit(self, name: str, frequency: str = "daily", **kwargs) -> Optional[Dict[str, Any]]:
        success = self.create_habit(name, frequency=frequency, **kwargs)
        if success:
            habit_id = self._find_habit_id(name)
            return self.habits.get(habit_id)
        return None
    
    def get_all_habits(self) -> List[Dict[str, Any]]:
        return self.list_habits(active_only=False)
    
    def log_habit(self, habit_id: str) -> bool:
        habit = self.habits.get(habit_id)
        if habit:
            return self.log_completion(habit['name'])
        return False
    
    def delete_habit(self, habit_id: str) -> bool:
        return self.remove_habit(habit_id)



    def remove_habit(self, habit_id: str) -> bool:
        if not self.enabled or habit_id not in self.habits:
            return False
        try:
            del self.habits[habit_id]
            del self.completions[habit_id]
            self._save_habits()
            logger.info(f"Removed habit: {habit_id}")
            return True
        except Exception as e:
            logger.error(f"Error removing habit: {e}")
            return False

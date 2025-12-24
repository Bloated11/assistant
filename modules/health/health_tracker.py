import logging
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import uuid

logger = logging.getLogger(__name__)

class HealthTracker:
    def __init__(self, config: dict):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.storage_path = config.get('storage_path', 'data/health.json')
        
        self.workouts = {}
        self.measurements = {}
        self.sleep_logs = {}
        self.water_intake = {}
        self.mood_logs = {}
        self.goals = {}
        
        if self.enabled:
            self._load_data()
        
        logger.info("HealthTracker initialized")
    
    def _load_data(self):
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.workouts = data.get('workouts', {})
                    self.measurements = data.get('measurements', {})
                    self.sleep_logs = data.get('sleep_logs', {})
                    self.water_intake = data.get('water_intake', {})
                    self.mood_logs = data.get('mood_logs', {})
                    self.goals = data.get('goals', {})
                logger.info(f"Loaded health data")
        except Exception as e:
            logger.error(f"Error loading health data: {e}")
    
    def _save_data(self):
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump({
                    'workouts': self.workouts,
                    'measurements': self.measurements,
                    'sleep_logs': self.sleep_logs,
                    'water_intake': self.water_intake,
                    'mood_logs': self.mood_logs,
                    'goals': self.goals,
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving health data: {e}")
    
    def log_workout(self, workout_type: str, duration: int, calories: int = None,
                   distance: float = None, notes: str = "", date: str = None) -> Optional[str]:
        if not self.enabled:
            return None
        
        try:
            workout_id = str(uuid.uuid4())[:8]
            workout_date = date or datetime.now().isoformat()
            
            self.workouts[workout_id] = {
                'id': workout_id,
                'type': workout_type,
                'duration': duration,
                'calories': calories,
                'distance': distance,
                'notes': notes,
                'date': workout_date,
                'created_at': datetime.now().isoformat()
            }
            
            self._save_data()
            logger.info(f"Logged workout: {workout_type}")
            return workout_id
            
        except Exception as e:
            logger.error(f"Error logging workout: {e}")
            return None
    
    def log_measurement(self, measurement_type: str, value: float, unit: str = "",
                       notes: str = "", date: str = None) -> Optional[str]:
        if not self.enabled:
            return None
        
        try:
            measurement_id = str(uuid.uuid4())[:8]
            measurement_date = date or datetime.now().isoformat()
            
            self.measurements[measurement_id] = {
                'id': measurement_id,
                'type': measurement_type,
                'value': float(value),
                'unit': unit,
                'notes': notes,
                'date': measurement_date,
                'created_at': datetime.now().isoformat()
            }
            
            self._save_data()
            logger.info(f"Logged measurement: {measurement_type} = {value} {unit}")
            return measurement_id
            
        except Exception as e:
            logger.error(f"Error logging measurement: {e}")
            return None
    
    def log_sleep(self, hours: float, quality: str = None, notes: str = "",
                 date: str = None) -> Optional[str]:
        if not self.enabled:
            return None
        
        try:
            sleep_id = str(uuid.uuid4())[:8]
            sleep_date = date or datetime.now().date().isoformat()
            
            self.sleep_logs[sleep_id] = {
                'id': sleep_id,
                'hours': float(hours),
                'quality': quality,
                'notes': notes,
                'date': sleep_date,
                'created_at': datetime.now().isoformat()
            }
            
            self._save_data()
            logger.info(f"Logged sleep: {hours} hours")
            return sleep_id
            
        except Exception as e:
            logger.error(f"Error logging sleep: {e}")
            return None
    
    def log_water(self, amount: float, unit: str = "ml", date: str = None) -> bool:
        if not self.enabled:
            return False
        
        try:
            water_date = date or datetime.now().date().isoformat()
            
            if water_date not in self.water_intake:
                self.water_intake[water_date] = {'total': 0.0, 'unit': unit, 'logs': []}
            
            self.water_intake[water_date]['total'] += float(amount)
            self.water_intake[water_date]['logs'].append({
                'amount': float(amount),
                'time': datetime.now().isoformat()
            })
            
            self._save_data()
            logger.info(f"Logged water: {amount} {unit}")
            return {"measurement_id": measurement_id, "type": measurement_type, "value": value, "unit": unit}
            
        except Exception as e:
            logger.error(f"Error logging water: {e}")
            return False
    
    def log_mood(self, mood: str, rating: int, notes: str = "", date: str = None) -> Optional[str]:
        if not self.enabled:
            return None
        
        try:
            mood_id = str(uuid.uuid4())[:8]
            mood_date = date or datetime.now().isoformat()
            
            self.mood_logs[mood_id] = {
                'id': mood_id,
                'mood': mood,
                'rating': max(1, min(10, int(rating))),
                'notes': notes,
                'date': mood_date,
                'created_at': datetime.now().isoformat()
            }
            
            self._save_data()
            logger.info(f"Logged mood: {mood} ({rating}/10)")
            return mood_id
            
        except Exception as e:
            logger.error(f"Error logging mood: {e}")
            return None
    
    def set_health_goal(self, goal_type: str, target_value: float, unit: str = "",
                       deadline: str = None) -> Optional[str]:
        if not self.enabled:
            return None
        
        try:
            goal_id = str(uuid.uuid4())[:8]
            
            self.goals[goal_id] = {
                'id': goal_id,
                'type': goal_type,
                'target_value': float(target_value),
                'unit': unit,
                'deadline': deadline,
                'created_at': datetime.now().isoformat(),
                'status': 'active'
            }
            
            self._save_data()
            logger.info(f"Set health goal: {goal_type} = {target_value} {unit}")
            return goal_id
            
        except Exception as e:
            logger.error(f"Error setting health goal: {e}")
            return None
    
    def get_workout_summary(self, days: int = 7) -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None
        
        try:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            recent_workouts = [w for w in self.workouts.values() 
                             if w['date'] >= cutoff]
            
            total_duration = sum(w['duration'] for w in recent_workouts)
            total_calories = sum(w.get('calories', 0) for w in recent_workouts if w.get('calories'))
            total_distance = sum(w.get('distance', 0) for w in recent_workouts if w.get('distance'))
            
            workout_types = defaultdict(int)
            for w in recent_workouts:
                workout_types[w['type']] += 1
            
            return {
                'period_days': days,
                'total_workouts': len(recent_workouts),
                'total_duration': total_duration,
                'total_calories': total_calories,
                'total_distance': total_distance,
                'workout_types': dict(workout_types),
                'avg_duration': total_duration / len(recent_workouts) if recent_workouts else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting workout summary: {e}")
            return None
    
    def get_sleep_summary(self, days: int = 7) -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None
        
        try:
            cutoff = (datetime.now() - timedelta(days=days)).date().isoformat()
            recent_sleep = [s for s in self.sleep_logs.values() 
                           if s['date'] >= cutoff]
            
            total_hours = sum(s['hours'] for s in recent_sleep)
            quality_counts = defaultdict(int)
            for s in recent_sleep:
                if s.get('quality'):
                    quality_counts[s['quality']] += 1
            
            return {
                'period_days': days,
                'total_nights': len(recent_sleep),
                'total_hours': total_hours,
                'avg_hours': total_hours / len(recent_sleep) if recent_sleep else 0,
                'quality_distribution': dict(quality_counts)
            }
            
        except Exception as e:
            logger.error(f"Error getting sleep summary: {e}")
            return None
    
    def get_today_water(self) -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None
        
        try:
            today = datetime.now().date().isoformat()
            if today in self.water_intake:
                return {
                    'total': self.water_intake[today]['total'],
                    'unit': self.water_intake[today]['unit'],
                    'logs_count': len(self.water_intake[today]['logs'])
                }
            return {'total': 0, 'unit': 'ml', 'logs_count': 0}
            
        except Exception as e:
            logger.error(f"Error getting water intake: {e}")
            return None
    
    def get_measurement_history(self, measurement_type: str, days: int = 30) -> List[Dict[str, Any]]:
        if not self.enabled:
            return []
        
        try:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            history = [m for m in self.measurements.values() 
                      if m['type'] == measurement_type and m['date'] >= cutoff]
            
            return sorted(history, key=lambda x: x['date'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error getting measurement history: {e}")
            return []
    
    def get_mood_analytics(self, days: int = 30) -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None
        
        try:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            recent_moods = [m for m in self.mood_logs.values() 
                           if m['date'] >= cutoff]
            
            if not recent_moods:
                return None
            
            ratings = [m['rating'] for m in recent_moods]
            mood_counts = defaultdict(int)
            for m in recent_moods:
                mood_counts[m['mood']] += 1
            
            return {
                'period_days': days,
                'total_logs': len(recent_moods),
                'avg_rating': sum(ratings) / len(ratings),
                'min_rating': min(ratings),
                'max_rating': max(ratings),
                'mood_distribution': dict(mood_counts)
            }
            
        except Exception as e:
            logger.error(f"Error getting mood analytics: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            'enabled': self.enabled,
            'total_workouts': len(self.workouts),
            'total_measurements': len(self.measurements),
            'total_sleep_logs': len(self.sleep_logs),
            'total_mood_logs': len(self.mood_logs),
            'active_goals': len([g for g in self.goals.values() if g['status'] == 'active'])
        }
    def log_weight(self, weight: float, unit: str = "kg"):
        return self.add_weight_entry(weight, unit)




    def add_weight_entry(self, weight: float, unit: str = "kg", **kwargs) -> Dict[str, Any]:
        measurement_id = self.log_measurement('weight', weight, unit, **kwargs)
        if measurement_id:
            return self.measurements[measurement_id].copy()
        return None


    def get_summary(self, days: int = 7) -> Dict[str, Any]:
        return {
            'workout_summary': self.get_workout_summary(days),
            'sleep_summary': self.get_sleep_summary(days),
            'mood_analytics': self.get_mood_analytics(days),
            'today_water': self.get_today_water(),
            'stats': self.get_stats()
        }

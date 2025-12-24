import logging
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import uuid

logger = logging.getLogger(__name__)

class LearningTrackerModule:
    def __init__(self, config: dict):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.storage_path = config.get('storage_path', 'data/learning.json')
        
        self.courses = {}
        self.skills = {}
        self.learning_sessions = {}
        self.resources = {}
        self.certifications = {}
        
        if self.enabled:
            self._load_data()
        
        logger.info("LearningTrackerModule initialized")
    
    def _load_data(self):
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.courses = data.get('courses', {})
                    self.skills = data.get('skills', {})
                    self.learning_sessions = data.get('learning_sessions', {})
                    self.resources = data.get('resources', {})
                    self.certifications = data.get('certifications', {})
                logger.info(f"Loaded learning data")
        except Exception as e:
            logger.error(f"Error loading learning data: {e}")
    
    def _save_data(self):
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump({
                    'courses': self.courses,
                    'skills': self.skills,
                    'learning_sessions': self.learning_sessions,
                    'resources': self.resources,
                    'certifications': self.certifications,
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving learning data: {e}")
    
    def add_course(self, name: str, platform: str = None, instructor: str = None,
                  duration: int = None, difficulty: str = None, category: str = None,
                  url: str = None) -> Optional[str]:
        if not self.enabled:
            return None
        
        try:
            course_id = str(uuid.uuid4())[:8]
            
            self.courses[course_id] = {
                'id': course_id,
                'name': name,
                'platform': platform,
                'instructor': instructor,
                'duration': duration,
                'difficulty': difficulty,
                'category': category,
                'url': url,
                'status': 'not_started',
                'progress': 0,
                'started_at': None,
                'completed_at': None,
                'rating': None,
                'notes': [],
                'created_at': datetime.now().isoformat()
            }
            
            self._save_data()
            logger.info(f"Added course: {name}")
            return self.courses[course_id].copy()
            
        except Exception as e:
            logger.error(f"Error adding course: {e}")
            return None
    
    def update_course_progress(self, course_id: str, progress: float) -> bool:
        if not self.enabled or course_id not in self.courses:
            return False
        
        try:
            self.courses[course_id]['progress'] = min(100.0, max(0.0, float(progress)))
            
            if self.courses[course_id]['status'] == 'not_started':
                self.courses[course_id]['status'] = 'in_progress'
                self.courses[course_id]['started_at'] = datetime.now().isoformat()
            
            if progress >= 100:
                self.courses[course_id]['status'] = 'completed'
                self.courses[course_id]['completed_at'] = datetime.now().isoformat()
            
            self._save_data()
            logger.info(f"Updated course {course_id} progress to {progress}%")
            return True
            
        except Exception as e:
            logger.error(f"Error updating course progress: {e}")
            return False
    
    def add_skill(self, name: str, category: str = None, proficiency: str = "beginner",
                 target_proficiency: str = None, related_courses: List[str] = None) -> Optional[str]:
        if not self.enabled:
            return None
        
        try:
            skill_id = str(uuid.uuid4())[:8]
            
            self.skills[skill_id] = {
                'id': skill_id,
                'name': name,
                'category': category,
                'proficiency': proficiency,
                'target_proficiency': target_proficiency,
                'related_courses': related_courses or [],
                'practice_hours': 0,
                'assessments': [],
                'milestones': [],
                'created_at': datetime.now().isoformat()
            }
            
            self._save_data()
            logger.info(f"Added skill: {name}")
            return skill_id
            
        except Exception as e:
            logger.error(f"Error adding skill: {e}")
            return None
    
    def update_skill_proficiency(self, skill_id: str, proficiency: str) -> bool:
        if not self.enabled or skill_id not in self.skills:
            return False
        
        try:
            self.skills[skill_id]['proficiency'] = proficiency
            self._save_data()
            logger.info(f"Updated skill {skill_id} proficiency to {proficiency}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating skill proficiency: {e}")
            return False
    
    def log_learning_session(self, course_id: str = None, skill_id: str = None,
                            duration: int = None, topic: str = None, 
                            notes: str = "") -> Optional[str]:
        if not self.enabled:
            return None
        
        try:
            session_id = str(uuid.uuid4())[:8]
            
            self.learning_sessions[session_id] = {
                'id': session_id,
                'course_id': course_id,
                'skill_id': skill_id,
                'duration': duration,
                'topic': topic,
                'notes': notes,
                'date': datetime.now().isoformat()
            }
            
            if skill_id and skill_id in self.skills and duration:
                self.skills[skill_id]['practice_hours'] += duration / 60
            
            self._save_data()
            logger.info(f"Logged learning session: {duration} minutes")
            return session_id
            
        except Exception as e:
            logger.error(f"Error logging learning session: {e}")
            return None
    
    def add_resource(self, title: str, resource_type: str, url: str = None,
                    category: str = None, skill_id: str = None, 
                    notes: str = "") -> Optional[str]:
        if not self.enabled:
            return None
        
        try:
            resource_id = str(uuid.uuid4())[:8]
            
            self.resources[resource_id] = {
                'id': resource_id,
                'title': title,
                'type': resource_type,
                'url': url,
                'category': category,
                'skill_id': skill_id,
                'notes': notes,
                'completed': False,
                'created_at': datetime.now().isoformat()
            }
            
            self._save_data()
            logger.info(f"Added resource: {title}")
            return resource_id
            
        except Exception as e:
            logger.error(f"Error adding resource: {e}")
            return None
    
    def add_certification(self, name: str, issuer: str, date_earned: str,
                         expiry_date: str = None, credential_id: str = None,
                         url: str = None) -> Optional[str]:
        if not self.enabled:
            return None
        
        try:
            cert_id = str(uuid.uuid4())[:8]
            
            self.certifications[cert_id] = {
                'id': cert_id,
                'name': name,
                'issuer': issuer,
                'date_earned': date_earned,
                'expiry_date': expiry_date,
                'credential_id': credential_id,
                'url': url,
                'created_at': datetime.now().isoformat()
            }
            
            self._save_data()
            logger.info(f"Added certification: {name}")
            return cert_id
            
        except Exception as e:
            logger.error(f"Error adding certification: {e}")
            return None
    
    def get_course(self, course_id: str) -> Optional[Dict[str, Any]]:
        if not self.enabled or course_id not in self.courses:
            return None
        return self.courses[course_id].copy()
    
    def get_skill(self, skill_id: str) -> Optional[Dict[str, Any]]:
        if not self.enabled or skill_id not in self.skills:
            return None
        
        skill = self.skills[skill_id].copy()
        
        sessions = [s for s in self.learning_sessions.values() 
                   if s.get('skill_id') == skill_id]
        skill['total_sessions'] = len(sessions)
        
        return skill
    
    def search_courses(self, query: str = None, status: str = None,
                      category: str = None, platform: str = None) -> List[Dict[str, Any]]:
        if not self.enabled:
            return []
        
        try:
            results = list(self.courses.values())
            
            if query:
                query_lower = query.lower()
                results = [c for c in results if query_lower in c['name'].lower()]
            
            if status:
                results = [c for c in results if c['status'] == status]
            
            if category:
                results = [c for c in results if c.get('category') == category]
            
            if platform:
                results = [c for c in results if c.get('platform') == platform]
            
            return sorted(results, key=lambda x: x['created_at'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error searching courses: {e}")
            return []
    
    def get_learning_stats(self, days: int = 30) -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None
        
        try:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            recent_sessions = [s for s in self.learning_sessions.values() 
                             if s['date'] >= cutoff]
            
            total_time = sum(s.get('duration', 0) for s in recent_sessions)
            
            courses_in_progress = len([c for c in self.courses.values() 
                                      if c['status'] == 'in_progress'])
            courses_completed = len([c for c in self.courses.values() 
                                    if c['status'] == 'completed'])
            
            skill_categories = defaultdict(int)
            for skill in self.skills.values():
                if skill.get('category'):
                    skill_categories[skill['category']] += 1
            
            return {
                'period_days': days,
                'total_sessions': len(recent_sessions),
                'total_time': total_time,
                'avg_session_time': total_time / len(recent_sessions) if recent_sessions else 0,
                'courses_in_progress': courses_in_progress,
                'courses_completed': courses_completed,
                'total_skills': len(self.skills),
                'skill_categories': dict(skill_categories),
                'total_certifications': len(self.certifications)
            }
            
        except Exception as e:
            logger.error(f"Error getting learning stats: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            'enabled': self.enabled,
            'total_courses': len(self.courses),
            'total_skills': len(self.skills),
            'total_sessions': len(self.learning_sessions),
            'total_resources': len(self.resources),
            'total_certifications': len(self.certifications)
        }
    
    def get_all_courses(self):
        return self.list_courses()

    
    
    def delete_course(self, course_id: str) -> bool:
        if not self.enabled or course_id not in self.courses:
            return False
        del self.courses[course_id]
        self._save_data()
        return True

    def list_courses(self, **kwargs):
        return self.search_courses(**kwargs)


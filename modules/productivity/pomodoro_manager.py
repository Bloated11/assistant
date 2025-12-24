import logging
import time
import threading
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
import json
import os

logger = logging.getLogger(__name__)

class PomodoroManager:
    def __init__(self, config: dict):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.work_duration = config.get('work_duration', 25)
        self.short_break = config.get('short_break', 5)
        self.long_break = config.get('long_break', 15)
        self.sessions_until_long_break = config.get('sessions_until_long_break', 4)
        self.storage_path = config.get('storage_path', 'data/pomodoro_history.json')
        
        self.current_session = None
        self.session_count = 0
        self.timer_thread = None
        self.is_running = False
        self.is_paused = False
        self.pause_time = None
        self.time_remaining = 0
        self.on_complete_callback = None
        
        self.history = []
        self._load_history()
        
        logger.info(f"PomodoroManager initialized ({self.work_duration}m work / {self.short_break}m break)")
    
    def _load_history(self):
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.history = data.get('history', [])
                    self.session_count = data.get('session_count', 0)
        except Exception as e:
            logger.error(f"Error loading pomodoro history: {e}")
    
    def _save_history(self):
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump({
                    'history': self.history[-100:],
                    'session_count': self.session_count,
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving pomodoro history: {e}")
    
    def start_session(self, session_type: str = 'work', duration: int = None, on_complete: Callable = None) -> bool:
        if not self.enabled:
            return False
        
        if self.is_running and not self.is_paused:
            logger.warning("Session already running")
            return False
        
        if duration is None:
            if session_type == 'work':
                duration = self.work_duration
            elif session_type == 'short_break':
                duration = self.short_break
            elif session_type == 'long_break':
                duration = self.long_break
            else:
                duration = self.work_duration
        
        self.current_session = {
            'type': session_type,
            'duration': duration,
            'start_time': datetime.now().isoformat(),
            'end_time': (datetime.now() + timedelta(minutes=duration)).isoformat()
        }
        
        self.time_remaining = duration * 60
        self.is_running = True
        self.is_paused = False
        self.on_complete_callback = on_complete
        
        self.timer_thread = threading.Thread(target=self._run_timer, daemon=True)
        self.timer_thread.start()
        
        logger.info(f"Started {session_type} session for {duration} minutes")
        return True
    
    def _run_timer(self):
        while self.time_remaining > 0 and self.is_running:
            if not self.is_paused:
                time.sleep(1)
                self.time_remaining -= 1
            else:
                time.sleep(0.1)
        
        if self.is_running and self.time_remaining <= 0:
            self._complete_session()
    
    def _complete_session(self):
        if not self.current_session:
            return
        
        self.current_session['completed_at'] = datetime.now().isoformat()
        self.current_session['completed'] = True
        
        self.history.append(self.current_session)
        
        if self.current_session['type'] == 'work':
            self.session_count += 1
        
        self._save_history()
        
        if self.on_complete_callback:
            try:
                self.on_complete_callback(self.current_session)
            except Exception as e:
                logger.error(f"Error in completion callback: {e}")
        
        logger.info(f"Completed {self.current_session['type']} session")
        
        self.is_running = False
        self.current_session = None
    
    def pause(self) -> bool:
        if not self.is_running or self.is_paused:
            return False
        
        self.is_paused = True
        self.pause_time = datetime.now()
        logger.info("Pomodoro paused")
        return True
    
    def resume(self) -> bool:
        if not self.is_running or not self.is_paused:
            return False
        
        self.is_paused = False
        self.pause_time = None
        logger.info("Pomodoro resumed")
        return True
    
    def stop(self) -> bool:
        if not self.is_running:
            return False
        
        if self.current_session:
            self.current_session['stopped_at'] = datetime.now().isoformat()
            self.current_session['completed'] = False
            self.history.append(self.current_session)
            self._save_history()
        
        self.is_running = False
        self.is_paused = False
        self.current_session = None
        self.time_remaining = 0
        
        logger.info("Pomodoro stopped")
        return True
    
    def get_status(self) -> Dict[str, Any]:
        if not self.enabled:
            return {'enabled': False}
        
        status = {
            'enabled': True,
            'is_running': self.is_running,
            'is_paused': self.is_paused,
            'session_count': self.session_count,
            'current_session': None,
            'time_remaining': 0,
            'progress_percent': 0
        }
        
        if self.current_session and self.is_running:
            minutes_remaining = self.time_remaining // 60
            seconds_remaining = self.time_remaining % 60
            
            total_seconds = self.current_session['duration'] * 60
            progress = ((total_seconds - self.time_remaining) / total_seconds) * 100
            
            status['current_session'] = {
                'type': self.current_session['type'],
                'duration': self.current_session['duration'],
                'started': self.current_session['start_time']
            }
            status['time_remaining'] = f"{minutes_remaining}:{seconds_remaining:02d}"
            status['progress_percent'] = round(progress, 1)
        
        return status
    
    def get_next_session_type(self) -> str:
        if self.session_count % self.sessions_until_long_break == 0 and self.session_count > 0:
            return 'long_break'
        return 'short_break'
    
    def start_work_session(self) -> bool:
        return self.start_session('work')
    
    def start_break(self) -> bool:
        break_type = self.get_next_session_type()
        return self.start_session(break_type)
    
    def get_today_stats(self) -> Dict[str, Any]:
        today = datetime.now().date()
        
        today_sessions = [
            s for s in self.history
            if datetime.fromisoformat(s['start_time']).date() == today
        ]
        
        completed = [s for s in today_sessions if s.get('completed', False)]
        work_sessions = [s for s in completed if s['type'] == 'work']
        break_sessions = [s for s in completed if s['type'] in ['short_break', 'long_break']]
        
        total_work_time = sum(s['duration'] for s in work_sessions)
        total_break_time = sum(s['duration'] for s in break_sessions)
        
        return {
            'date': today.isoformat(),
            'total_sessions': len(completed),
            'work_sessions': len(work_sessions),
            'break_sessions': len(break_sessions),
            'total_work_minutes': total_work_time,
            'total_break_minutes': total_break_time,
            'focus_score': min(100, (len(work_sessions) / 8) * 100) if work_sessions else 0
        }
    
    def get_week_stats(self) -> Dict[str, Any]:
        now = datetime.now()
        week_ago = now - timedelta(days=7)
        
        week_sessions = [
            s for s in self.history
            if datetime.fromisoformat(s['start_time']) >= week_ago
        ]
        
        completed = [s for s in week_sessions if s.get('completed', False)]
        work_sessions = [s for s in completed if s['type'] == 'work']
        
        total_work_time = sum(s['duration'] for s in work_sessions)
        avg_per_day = total_work_time / 7 if work_sessions else 0
        
        return {
            'period': 'last_7_days',
            'total_work_sessions': len(work_sessions),
            'total_work_minutes': total_work_time,
            'average_minutes_per_day': round(avg_per_day, 1),
            'most_productive_day': self._get_most_productive_day(week_sessions)
        }
    
    def _get_most_productive_day(self, sessions: list) -> str:
        day_counts = {}
        
        for session in sessions:
            if session.get('completed') and session['type'] == 'work':
                day = datetime.fromisoformat(session['start_time']).strftime('%A')
                day_counts[day] = day_counts.get(day, 0) + 1
        
        if not day_counts:
            return "N/A"
        
        return max(day_counts, key=day_counts.get)

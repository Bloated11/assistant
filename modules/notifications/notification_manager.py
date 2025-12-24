import logging
from typing import Dict, Any, List
from datetime import datetime
import subprocess

logger = logging.getLogger(__name__)

class NotificationManager:
    def __init__(self, config: dict):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.desktop_notifications = config.get('desktop_notifications', True)
        self.sound_alerts = config.get('sound_alerts', True)
        self.priority_filter = config.get('priority_filter', 'medium')
        
        self.notification_history = []
        
        logger.info(f"NotificationManager initialized (enabled: {self.enabled})")
    
    def send_notification(self, title: str, message: str, priority: str = 'normal', icon: str = None):
        if not self.enabled:
            return False
        
        if not self._should_notify(priority):
            return False
        
        self._save_to_history(title, message, priority)
        
        if self.desktop_notifications:
            self._send_desktop_notification(title, message, icon)
        
        if self.sound_alerts and priority in ['high', 'critical']:
            self._play_sound()
        
        return True
    
    def _should_notify(self, priority: str) -> bool:
        priority_levels = {
            'low': 0,
            'normal': 1,
            'medium': 2,
            'high': 3,
            'critical': 4
        }
        
        filter_level = priority_levels.get(self.priority_filter, 1)
        notify_level = priority_levels.get(priority, 1)
        
        return notify_level >= filter_level
    
    def _send_desktop_notification(self, title: str, message: str, icon: str = None):
        try:
            cmd = ['notify-send', title, message]
            
            if icon:
                cmd.extend(['-i', icon])
            
            subprocess.run(cmd, check=False)
            logger.info(f"Desktop notification sent: {title}")
            
        except Exception as e:
            logger.error(f"Error sending desktop notification: {e}")
    
    def _play_sound(self):
        try:
            subprocess.run(['paplay', '/usr/share/sounds/freedesktop/stereo/message.oga'], 
                         check=False, 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL)
        except:
            pass
    
    def _save_to_history(self, title: str, message: str, priority: str):
        self.notification_history.append({
            'title': title,
            'message': message,
            'priority': priority,
            'timestamp': datetime.now().isoformat()
        })
        
        if len(self.notification_history) > 100:
            self.notification_history = self.notification_history[-100:]
    
    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self.notification_history[-limit:]
    
    def clear_history(self):
        self.notification_history = []
        logger.info("Notification history cleared")
    
    def notify_task_due(self, task_title: str):
        self.send_notification(
            "Task Due",
            f"Task '{task_title}' is due now!",
            priority='high',
            icon='calendar'
        )
    
    def notify_system_alert(self, message: str):
        self.send_notification(
            "System Alert",
            message,
            priority='critical',
            icon='dialog-warning'
        )
    
    def notify_email_received(self, sender: str, subject: str):
        self.send_notification(
            f"New Email from {sender}",
            subject,
            priority='normal',
            icon='mail-unread'
        )

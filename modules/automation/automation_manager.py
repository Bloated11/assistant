import logging
import time
from typing import Callable, Dict, Any, List
from datetime import datetime

try:
    import schedule
    SCHEDULE_AVAILABLE = True
except ImportError:
    SCHEDULE_AVAILABLE = False
    logging.warning("schedule module not available - scheduling features disabled")

try:
    from .system_control import SystemControl
except ImportError:
    SystemControl = None
    logging.warning("SystemControl not available")

logger = logging.getLogger(__name__)

class AutomationManager:
    def __init__(self, config: dict):
        self.config = config
        self.enabled = config.get('enabled', True) and SCHEDULE_AVAILABLE
        self.system_control = SystemControl(config) if SystemControl else None
        self.scheduled_tasks = []
        self.running = False
        
        if not SCHEDULE_AVAILABLE:
            logger.warning("AutomationManager initialized with limited functionality (schedule module not found)")
        else:
            logger.info("AutomationManager initialized")
    
    def schedule_task(self, name: str, func: Callable, interval: str, time_str: str = None):
        if not SCHEDULE_AVAILABLE:
            logger.warning("Scheduling not available - schedule module not installed")
            return False
            
        try:
            job = None
            
            if interval == 'daily' and time_str:
                job = schedule.every().day.at(time_str).do(func)
            elif interval == 'hourly':
                job = schedule.every().hour.do(func)
            elif interval.endswith('minutes'):
                minutes = int(interval.split()[0])
                job = schedule.every(minutes).minutes.do(func)
            elif interval.endswith('seconds'):
                seconds = int(interval.split()[0])
                job = schedule.every(seconds).seconds.do(func)
            
            if job:
                self.scheduled_tasks.append({
                    'name': name,
                    'job': job,
                    'interval': interval,
                    'time': time_str,
                    'created': datetime.now()
                })
                logger.info(f"Scheduled task: {name} ({interval})")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error scheduling task {name}: {e}")
            return False
    
    def run_scheduler(self):
        self.running = True
        logger.info("Starting scheduler")
        
        while self.running:
            schedule.run_pending()
            time.sleep(1)
    
    def stop_scheduler(self):
        self.running = False
        logger.info("Stopping scheduler")
    
    def list_scheduled_tasks(self) -> List[Dict[str, Any]]:
        return [{
            'name': task['name'],
            'interval': task['interval'],
            'time': task['time'],
            'next_run': task['job'].next_run
        } for task in self.scheduled_tasks]
    
    def cancel_task(self, name: str) -> bool:
        for task in self.scheduled_tasks:
            if task['name'] == name:
                schedule.cancel_job(task['job'])
                self.scheduled_tasks.remove(task)
                logger.info(f"Cancelled task: {name}")
                return True
        return False
    
    def execute_system_command(self, command: str) -> Dict[str, Any]:
        return self.system_control.execute_command(command)
    
    def get_system_status(self) -> Dict[str, Any]:
        return self.system_control.get_system_info()

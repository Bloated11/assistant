import logging
import os
import subprocess
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class FocusModeManager:
    def __init__(self, config: dict):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.block_websites = config.get('block_websites', True)
        self.block_apps = config.get('block_apps', False)
        self.mute_notifications = config.get('mute_notifications', True)
        self.storage_path = config.get('storage_path', 'data/focus_sessions.json')
        
        self.is_active = False
        self.start_time = None
        self.blocked_sites = []
        self.blocked_apps = []
        self.original_hosts = None
        
        self.default_blocked_sites = [
            'facebook.com',
            'twitter.com',
            'instagram.com',
            'youtube.com',
            'reddit.com',
            'tiktok.com'
        ]
        
        self.sessions = []
        self._load_sessions()
        
        logger.info("FocusModeManager initialized")
    
    def _load_sessions(self):
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.sessions = data.get('sessions', [])
        except Exception as e:
            logger.error(f"Error loading focus sessions: {e}")
    
    def _save_sessions(self):
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump({
                    'sessions': self.sessions[-50:],
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving focus sessions: {e}")
    
    def activate(self, custom_sites: List[str] = None, custom_apps: List[str] = None) -> bool:
        if not self.enabled:
            return False
        
        if self.is_active:
            logger.warning("Focus mode already active")
            return False
        
        self.start_time = datetime.now()
        self.is_active = True
        
        sites_to_block = custom_sites if custom_sites else self.default_blocked_sites
        apps_to_block = custom_apps if custom_apps else []
        
        success = True
        
        if self.block_websites:
            if self._block_websites(sites_to_block):
                self.blocked_sites = sites_to_block
                logger.info(f"Blocked {len(sites_to_block)} websites")
            else:
                success = False
        
        if self.block_apps and apps_to_block:
            if self._block_applications(apps_to_block):
                self.blocked_apps = apps_to_block
                logger.info(f"Blocked {len(apps_to_block)} applications")
            else:
                success = False
        
        if self.mute_notifications:
            self._mute_system_notifications()
        
        logger.info("Focus mode activated")
        return True
    
    def deactivate(self) -> bool:
        if not self.is_active:
            return False
        
        if self.blocked_sites:
            self._unblock_websites()
            self.blocked_sites = []
        
        if self.blocked_apps:
            self._unblock_applications()
            self.blocked_apps = []
        
        if self.mute_notifications:
            self._unmute_system_notifications()
        
        duration = (datetime.now() - self.start_time).total_seconds() / 60
        
        self.sessions.append({
            'start_time': self.start_time.isoformat(),
            'end_time': datetime.now().isoformat(),
            'duration_minutes': round(duration, 1)
        })
        
        self._save_sessions()
        
        self.is_active = False
        self.start_time = None
        
        logger.info(f"Focus mode deactivated (duration: {duration:.1f} minutes)")
        return True
    
    def _block_websites(self, sites: List[str]) -> bool:
        try:
            if os.name == 'nt':
                hosts_path = r'C:\Windows\System32\drivers\etc\hosts'
            else:
                hosts_path = '/etc/hosts'
            
            if not os.path.exists(hosts_path):
                logger.warning(f"Hosts file not found: {hosts_path}")
                return False
            
            try:
                with open(hosts_path, 'r') as f:
                    self.original_hosts = f.read()
            except PermissionError:
                logger.warning("No permission to modify hosts file. Run with sudo/admin privileges for website blocking.")
                return False
            
            with open(hosts_path, 'a') as f:
                f.write('\n# Focus Mode - Blocked Sites\n')
                for site in sites:
                    f.write(f'127.0.0.1 {site}\n')
                    f.write(f'127.0.0.1 www.{site}\n')
                f.write('# End Focus Mode\n')
            
            return True
            
        except Exception as e:
            logger.error(f"Error blocking websites: {e}")
            return False
    
    def _unblock_websites(self) -> bool:
        try:
            if os.name == 'nt':
                hosts_path = r'C:\Windows\System32\drivers\etc\hosts'
            else:
                hosts_path = '/etc/hosts'
            
            if not os.path.exists(hosts_path):
                return False
            
            try:
                with open(hosts_path, 'r') as f:
                    lines = f.readlines()
                
                filtered_lines = []
                skip = False
                
                for line in lines:
                    if '# Focus Mode - Blocked Sites' in line:
                        skip = True
                    elif '# End Focus Mode' in line:
                        skip = False
                        continue
                    elif not skip:
                        filtered_lines.append(line)
                
                with open(hosts_path, 'w') as f:
                    f.writelines(filtered_lines)
                
                return True
                
            except PermissionError:
                logger.warning("No permission to modify hosts file")
                return False
            
        except Exception as e:
            logger.error(f"Error unblocking websites: {e}")
            return False
    
    def _block_applications(self, apps: List[str]) -> bool:
        try:
            for app in apps:
                if os.name == 'nt':
                    subprocess.run(['taskkill', '/F', '/IM', app], capture_output=True)
                else:
                    subprocess.run(['pkill', '-f', app], capture_output=True)
            return True
        except Exception as e:
            logger.error(f"Error blocking applications: {e}")
            return False
    
    def _unblock_applications(self) -> bool:
        return True
    
    def _mute_system_notifications(self) -> bool:
        try:
            if os.name == 'posix':
                subprocess.run(['notify-send', '-u', 'low', 'Focus Mode', 'Notifications muted'], capture_output=True)
            return True
        except Exception as e:
            logger.error(f"Error muting notifications: {e}")
            return False
    
    def _unmute_system_notifications(self) -> bool:
        try:
            if os.name == 'posix':
                subprocess.run(['notify-send', '-u', 'normal', 'Focus Mode', 'Notifications restored'], capture_output=True)
            return True
        except Exception as e:
            logger.error(f"Error unmuting notifications: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        if not self.enabled:
            return {'enabled': False}
        
        status = {
            'enabled': True,
            'is_active': self.is_active,
            'blocked_sites_count': len(self.blocked_sites),
            'blocked_apps_count': len(self.blocked_apps),
            'duration_minutes': 0
        }
        
        if self.is_active and self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds() / 60
            status['duration_minutes'] = round(duration, 1)
            status['start_time'] = self.start_time.isoformat()
        
        return status
    
    def get_stats(self) -> Dict[str, Any]:
        total_sessions = len(self.sessions)
        total_minutes = sum(s['duration_minutes'] for s in self.sessions)
        avg_duration = total_minutes / total_sessions if total_sessions > 0 else 0
        
        return {
            'total_sessions': total_sessions,
            'total_focus_minutes': round(total_minutes, 1),
            'average_session_duration': round(avg_duration, 1),
            'longest_session': max((s['duration_minutes'] for s in self.sessions), default=0)
        }
    
    def add_blocked_site(self, site: str) -> bool:
        if site not in self.default_blocked_sites:
            self.default_blocked_sites.append(site)
            
            if self.is_active:
                return self._block_websites([site])
            
            return True
        return False
    
    def remove_blocked_site(self, site: str) -> bool:
        if site in self.default_blocked_sites:
            self.default_blocked_sites.remove(site)
            return True
        return False
    
    def get_blocked_sites(self) -> List[str]:
        return self.default_blocked_sites.copy()
    
    def start_focus_session(self, name: str = "Focus Session", duration: int = 25) -> bool:
        return self.activate()
    
    def stop_focus_session(self) -> bool:
        return self.deactivate()

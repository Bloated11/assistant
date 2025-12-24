import os
import subprocess
import psutil
import logging
from typing import Dict, List, Optional, Any
import platform
import shutil

logger = logging.getLogger(__name__)

class SystemControl:
    def __init__(self, config: dict):
        self.config = config
        self.allowed_commands = config.get('allowed_commands', [])
        self.require_confirmation = config.get('require_confirmation', True)
        self.system = platform.system()
        
        logger.info(f"SystemControl initialized for {self.system}")
    
    def execute_command(self, command: str, shell: bool = True) -> Dict[str, Any]:
        try:
            logger.info(f"Executing command: {command}")
            
            result = subprocess.run(
                command,
                shell=shell,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            logger.error(f"Command timeout: {command}")
            return {'success': False, 'error': 'Command timeout'}
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_system_info(self) -> Dict[str, Any]:
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'platform': self.system,
                'cpu_percent': cpu_percent,
                'cpu_count': psutil.cpu_count(),
                'memory_total_gb': round(memory.total / (1024**3), 2),
                'memory_used_gb': round(memory.used / (1024**3), 2),
                'memory_percent': memory.percent,
                'disk_total_gb': round(disk.total / (1024**3), 2),
                'disk_used_gb': round(disk.used / (1024**3), 2),
                'disk_percent': disk.percent
            }
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {}
    
    def list_processes(self, limit: int = 10) -> List[Dict[str, Any]]:
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
            return processes[:limit]
            
        except Exception as e:
            logger.error(f"Error listing processes: {e}")
            return []
    
    def kill_process(self, pid: int) -> bool:
        try:
            process = psutil.Process(pid)
            process.terminate()
            process.wait(timeout=3)
            logger.info(f"Process {pid} terminated")
            return True
        except Exception as e:
            logger.error(f"Error killing process {pid}: {e}")
            return False
    
    def open_application(self, app_name: str) -> bool:
        try:
            if self.system == 'Linux':
                subprocess.Popen([app_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif self.system == 'Windows':
                os.startfile(app_name)
            elif self.system == 'Darwin':
                subprocess.Popen(['open', '-a', app_name])
            
            logger.info(f"Opened application: {app_name}")
            return True
        except Exception as e:
            logger.error(f"Error opening application {app_name}: {e}")
            return False
    
    def file_operations(self, operation: str, source: str, destination: str = None) -> bool:
        try:
            if operation == 'copy' and destination:
                shutil.copy2(source, destination)
                logger.info(f"Copied {source} to {destination}")
                return True
            elif operation == 'move' and destination:
                shutil.move(source, destination)
                logger.info(f"Moved {source} to {destination}")
                return True
            elif operation == 'delete':
                if os.path.isfile(source):
                    os.remove(source)
                elif os.path.isdir(source):
                    shutil.rmtree(source)
                logger.info(f"Deleted {source}")
                return True
            elif operation == 'create_dir':
                os.makedirs(source, exist_ok=True)
                logger.info(f"Created directory {source}")
                return True
            
            return False
        except Exception as e:
            logger.error(f"File operation error: {e}")
            return False
    
    def get_network_info(self) -> Dict[str, Any]:
        try:
            net_io = psutil.net_io_counters()
            connections = len(psutil.net_connections())
            
            return {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv,
                'active_connections': connections
            }
        except Exception as e:
            logger.error(f"Error getting network info: {e}")
            return {}
    
    def shutdown_system(self, delay: int = 0):
        if self.system == 'Linux':
            os.system(f'shutdown -h +{delay}')
        elif self.system == 'Windows':
            os.system(f'shutdown /s /t {delay * 60}')
        elif self.system == 'Darwin':
            os.system(f'sudo shutdown -h +{delay}')
    
    def restart_system(self, delay: int = 0):
        if self.system == 'Linux':
            os.system(f'shutdown -r +{delay}')
        elif self.system == 'Windows':
            os.system(f'shutdown /r /t {delay * 60}')
        elif self.system == 'Darwin':
            os.system(f'sudo shutdown -r +{delay}')

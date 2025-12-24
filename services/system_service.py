import psutil
import platform
import os
import subprocess
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class SystemService:
    """Service for system information and monitoring"""
    
    def __init__(self, phenom):
        self.phenom = phenom
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            "cpu": self._get_cpu_info(),
            "memory": self._get_memory_info(),
            "disk": self._get_disk_info(),
            "gpu": self._get_gpu_info(),
            "ai": self._get_ai_status(),
            "modules": self._get_module_status(),
            "platform": self._get_platform_info()
        }
    
    def _get_cpu_info(self) -> Dict[str, Any]:
        """Get CPU information"""
        try:
            return {
                "cores": psutil.cpu_count(logical=False),
                "threads": psutil.cpu_count(logical=True),
                "usage_percent": psutil.cpu_percent(interval=1),
                "frequency": psutil.cpu_freq().current if psutil.cpu_freq() else None
            }
        except Exception as e:
            logger.error(f"Error getting CPU info: {e}")
            return {"error": str(e)}
    
    def _get_memory_info(self) -> Dict[str, Any]:
        """Get memory information"""
        try:
            mem = psutil.virtual_memory()
            return {
                "total_gb": round(mem.total / (1024**3), 2),
                "available_gb": round(mem.available / (1024**3), 2),
                "used_gb": round(mem.used / (1024**3), 2),
                "percent": mem.percent
            }
        except Exception as e:
            logger.error(f"Error getting memory info: {e}")
            return {"error": str(e)}
    
    def _get_disk_info(self) -> Dict[str, Any]:
        """Get disk information"""
        try:
            disk = psutil.disk_usage('/')
            return {
                "total_gb": round(disk.total / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "percent": disk.percent
            }
        except Exception as e:
            logger.error(f"Error getting disk info: {e}")
            return {"error": str(e)}
    
    def _get_gpu_info(self) -> Dict[str, Any]:
        """Get GPU information"""
        gpu_info = {
            "available": False,
            "type": "None",
            "details": None
        }
        
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=name,memory.total,memory.used,utilization.gpu', '--format=csv,noheader,nounits'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                parts = result.stdout.strip().split(',')
                if len(parts) >= 4:
                    gpu_info = {
                        "available": True,
                        "type": "NVIDIA",
                        "name": parts[0].strip(),
                        "memory_total_mb": int(parts[1].strip()),
                        "memory_used_mb": int(parts[2].strip()),
                        "utilization_percent": int(parts[3].strip())
                    }
        except FileNotFoundError:
            logger.debug("nvidia-smi not found")
        except Exception as e:
            logger.error(f"Error getting GPU info: {e}")
        
        if not gpu_info["available"]:
            try:
                result = subprocess.run(['lspci'], capture_output=True, text=True, timeout=5)
                if 'VGA' in result.stdout or 'Display' in result.stdout:
                    for line in result.stdout.split('\n'):
                        if 'VGA' in line or 'Display' in line:
                            if 'AMD' in line or 'Radeon' in line:
                                gpu_info = {"available": True, "type": "AMD", "details": line.strip()}
                                break
                            elif 'Intel' in line:
                                gpu_info = {"available": True, "type": "Intel Integrated", "details": line.strip()}
                                break
            except Exception as e:
                logger.debug(f"lspci check failed: {e}")
        
        return gpu_info
    
    def _get_ai_status(self) -> Dict[str, Any]:
        """Get AI system status"""
        try:
            local_llm = self.phenom.ai.local_llm
            cloud_llm = self.phenom.ai.cloud_llm
            
            status = {
                "mode": self.phenom.ai.mode,
                "local": {
                    "enabled": local_llm.enabled,
                    "available": local_llm.is_available() if local_llm.enabled else False,
                    "model": local_llm.model if local_llm.enabled else None,
                    "base_url": local_llm.base_url if local_llm.enabled else None
                },
                "cloud": {
                    "enabled": cloud_llm.enabled,
                    "available": cloud_llm.is_available() if cloud_llm.enabled else False,
                    "provider": cloud_llm.provider if cloud_llm.enabled else None,
                    "model": cloud_llm.model if cloud_llm.enabled else None
                }
            }
            
            if local_llm.enabled:
                try:
                    import requests
                    response = requests.get(f"{local_llm.base_url}/api/ps", timeout=2)
                    if response.status_code == 200:
                        models = response.json()
                        if models and isinstance(models, dict) and 'models' in models:
                            status["local"]["loaded_models"] = [m.get('name', 'Unknown') for m in models['models']]
                except Exception as e:
                    logger.debug(f"Could not fetch loaded models: {e}")
            
            return status
        except Exception as e:
            logger.error(f"Error getting AI status: {e}")
            return {"error": str(e)}
    
    def _get_module_status(self) -> Dict[str, Any]:
        """Get module status"""
        try:
            modules = {
                "tasks": hasattr(self.phenom, 'tasks'),
                "notes": hasattr(self.phenom, 'notes_manager'),
                "goals": hasattr(self.phenom, 'goal_tracker'),
                "habits": hasattr(self.phenom, 'habit_tracker'),
                "finance": hasattr(self.phenom, 'finance_tracker'),
                "voice": hasattr(self.phenom, 'voice'),
                "web_search": hasattr(self.phenom, 'web'),
                "database": hasattr(self.phenom, 'db')
            }
            
            if hasattr(self.phenom, 'voice'):
                modules["voice_enabled"] = self.phenom.voice.is_available()
            
            return {
                "total": len([v for v in modules.values() if v]),
                "details": modules
            }
        except Exception as e:
            logger.error(f"Error getting module status: {e}")
            return {"error": str(e)}
    
    def _get_platform_info(self) -> Dict[str, Any]:
        """Get platform information"""
        try:
            return {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "python_version": platform.python_version()
            }
        except Exception as e:
            logger.error(f"Error getting platform info: {e}")
            return {"error": str(e)}

import logging
import os
import subprocess
from typing import List, Dict, Any, Optional
import re
from pathlib import Path

logger = logging.getLogger(__name__)

class FileSearchEngine:
    def __init__(self, config: dict):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.search_paths = config.get('search_paths', [str(Path.home())])
        self.max_results = config.get('max_results', 50)
        self.exclude_dirs = config.get('exclude_dirs', [
            '.git', '__pycache__', 'node_modules', '.cache', 
            '.local/share/Trash', '.npm', '.venv', 'venv'
        ])
        self.file_extensions = config.get('file_extensions', [])
        
        self.has_locate = self._check_command('locate')
        self.has_fd = self._check_command('fd')
        
        logger.info(f"FileSearchEngine initialized (locate: {self.has_locate}, fd: {self.has_fd})")
    
    def _check_command(self, cmd: str) -> bool:
        try:
            result = subprocess.run(['which', cmd], capture_output=True, text=True, timeout=2)
            return result.returncode == 0
        except Exception:
            return False
    
    def search_by_name(self, filename: str, search_path: str = None) -> List[Dict[str, Any]]:
        if not self.enabled:
            return []
        
        path = search_path or self.search_paths[0]
        
        if self.has_fd:
            return self._search_with_fd(filename, path)
        else:
            return self._search_with_find(filename, path)
    
    def _search_with_fd(self, filename: str, path: str) -> List[Dict[str, Any]]:
        try:
            exclude_args = []
            for exclude_dir in self.exclude_dirs:
                exclude_args.extend(['-E', exclude_dir])
            
            cmd = ['fd', '-H', '-t', 'f', '--max-results', str(self.max_results)] + exclude_args + [filename, path]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                files = result.stdout.strip().split('\n')
                return self._format_results(files)
            else:
                logger.warning(f"fd search failed: {result.stderr}")
                return []
                
        except subprocess.TimeoutExpired:
            logger.error("fd search timeout")
            return []
        except Exception as e:
            logger.error(f"fd search error: {e}")
            return []
    
    def _search_with_find(self, filename: str, path: str) -> List[Dict[str, Any]]:
        try:
            exclude_args = []
            for exclude_dir in self.exclude_dirs:
                exclude_args.extend(['-not', '-path', f'*/{exclude_dir}/*'])
            
            cmd = ['find', path, '-type', 'f', '-iname', f'*{filename}*'] + exclude_args
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                files = result.stdout.strip().split('\n')
                files = [f for f in files if f][:self.max_results]
                return self._format_results(files)
            else:
                logger.warning(f"find search failed: {result.stderr}")
                return []
                
        except subprocess.TimeoutExpired:
            logger.error("find search timeout")
            return []
        except Exception as e:
            logger.error(f"find search error: {e}")
            return []
    
    def search_by_content(self, content: str, search_path: str = None, 
                         file_pattern: str = "*") -> List[Dict[str, Any]]:
        if not self.enabled:
            return []
        
        path = search_path or self.search_paths[0]
        
        try:
            exclude_args = []
            for exclude_dir in self.exclude_dirs:
                exclude_args.extend(['--exclude-dir', exclude_dir])
            
            cmd = ['grep', '-r', '-l', '-i'] + exclude_args + [content, path]
            
            if file_pattern != "*":
                cmd.extend(['--include', file_pattern])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                files = result.stdout.strip().split('\n')
                files = [f for f in files if f][:self.max_results]
                return self._format_results(files)
            else:
                return []
                
        except subprocess.TimeoutExpired:
            logger.error("grep search timeout")
            return []
        except Exception as e:
            logger.error(f"grep search error: {e}")
            return []
    
    def search_by_extension(self, extension: str, search_path: str = None) -> List[Dict[str, Any]]:
        if not self.enabled:
            return []
        
        path = search_path or self.search_paths[0]
        
        if not extension.startswith('.'):
            extension = f'.{extension}'
        
        try:
            exclude_args = []
            for exclude_dir in self.exclude_dirs:
                exclude_args.extend(['-not', '-path', f'*/{exclude_dir}/*'])
            
            cmd = ['find', path, '-type', 'f', '-name', f'*{extension}'] + exclude_args
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                files = result.stdout.strip().split('\n')
                files = [f for f in files if f][:self.max_results]
                return self._format_results(files)
            else:
                logger.warning(f"Extension search failed: {result.stderr}")
                return []
                
        except subprocess.TimeoutExpired:
            logger.error("Extension search timeout")
            return []
        except Exception as e:
            logger.error(f"Extension search error: {e}")
            return []
    
    def quick_locate(self, filename: str) -> List[Dict[str, Any]]:
        if not self.enabled or not self.has_locate:
            return []
        
        try:
            cmd = ['locate', '-i', '-l', str(self.max_results), filename]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                files = result.stdout.strip().split('\n')
                files = [f for f in files if f and not any(excl in f for excl in self.exclude_dirs)]
                return self._format_results(files)
            else:
                return []
                
        except subprocess.TimeoutExpired:
            logger.error("locate search timeout")
            return []
        except Exception as e:
            logger.error(f"locate search error: {e}")
            return []
    
    def _format_results(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        results = []
        
        for filepath in file_paths:
            if not filepath:
                continue
            
            try:
                path = Path(filepath)
                
                if not path.exists():
                    continue
                
                stat = path.stat()
                
                results.append({
                    'path': str(path.absolute()),
                    'name': path.name,
                    'size': stat.st_size,
                    'modified': stat.st_mtime,
                    'directory': str(path.parent),
                    'extension': path.suffix
                })
                
            except Exception as e:
                logger.debug(f"Error formatting {filepath}: {e}")
                continue
        
        return results
    
    def search(self, query: str, search_type: str = 'name', 
               search_path: str = None, file_pattern: str = "*") -> List[Dict[str, Any]]:
        if search_type == 'name':
            if self.has_locate and search_path is None:
                results = self.quick_locate(query)
                if results:
                    return results
            return self.search_by_name(query, search_path)
        
        elif search_type == 'content':
            return self.search_by_content(query, search_path, file_pattern)
        
        elif search_type == 'extension':
            return self.search_by_extension(query, search_path)
        
        else:
            logger.warning(f"Unknown search type: {search_type}")
            return []

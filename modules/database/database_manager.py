import sqlite3
import logging
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, config: dict):
        self.enabled = config.get('enabled', True)
        self.db_path = config.get('database_path', 'data/phenom.db')
        self.connection = None
        self.cursor = None
        
        if self.enabled:
            self._initialize_database()
    
    def _initialize_database(self):
        try:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
            self.cursor = self.connection.cursor()
            
            self._create_tables()
            logger.info(f"Database initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            self.enabled = False
    
    def _create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                priority TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'pending',
                due_date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT,
                tags TEXT
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_input TEXT NOT NULL,
                assistant_response TEXT NOT NULL,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                context TEXT
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                start_time TEXT NOT NULL,
                end_time TEXT,
                location TEXT,
                attendees TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE NOT NULL,
                filename TEXT NOT NULL,
                size INTEGER,
                file_type TEXT,
                category TEXT,
                tags TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                modified_at TEXT
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS automation_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                trigger_type TEXT NOT NULL,
                trigger_params TEXT,
                action_type TEXT NOT NULL,
                action_params TEXT,
                enabled INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.connection.commit()
    
    def insert_task(self, title: str, description: str = "", priority: str = "medium",
                   due_date: str = None, tags: List[str] = None) -> int:
        if not self.enabled:
            return -1
        
        try:
            tags_json = json.dumps(tags) if tags else None
            self.cursor.execute('''
                INSERT INTO tasks (title, description, priority, due_date, tags)
                VALUES (?, ?, ?, ?, ?)
            ''', (title, description, priority, due_date, tags_json))
            self.connection.commit()
            return self.cursor.lastrowid
        except Exception as e:
            logger.error(f"Error inserting task: {e}")
            return -1
    
    def get_tasks(self, status: str = None, priority: str = None) -> List[Dict]:
        if not self.enabled:
            return []
        
        try:
            query = "SELECT * FROM tasks WHERE 1=1"
            params = []
            
            if status:
                query += " AND status = ?"
                params.append(status)
            if priority:
                query += " AND priority = ?"
                params.append(priority)
            
            query += " ORDER BY created_at DESC"
            
            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()
            
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting tasks: {e}")
            return []
    
    def update_task_status(self, task_id: int, status: str) -> bool:
        if not self.enabled:
            return False
        
        try:
            completed_at = datetime.now().isoformat() if status == 'completed' else None
            self.cursor.execute('''
                UPDATE tasks SET status = ?, completed_at = ?
                WHERE id = ?
            ''', (status, completed_at, task_id))
            self.connection.commit()
            return self.cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating task: {e}")
            return False
    
    def delete_task(self, task_id: int) -> bool:
        if not self.enabled:
            return False
        
        try:
            self.cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
            self.connection.commit()
            return self.cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting task: {e}")
            return False
    
    def store_memory(self, key: str, value: str, category: str = "general") -> bool:
        if not self.enabled:
            return False
        
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO memory (key, value, category, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (key, value, category))
            self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Error storing memory: {e}")
            return False
    
    def recall_memory(self, key: str) -> Optional[str]:
        if not self.enabled:
            return None
        
        try:
            self.cursor.execute('SELECT value FROM memory WHERE key = ?', (key,))
            row = self.cursor.fetchone()
            return row['value'] if row else None
        except Exception as e:
            logger.error(f"Error recalling memory: {e}")
            return None
    
    def get_memories(self, category: str = None) -> List[Dict]:
        if not self.enabled:
            return []
        
        try:
            if category:
                self.cursor.execute('SELECT * FROM memory WHERE category = ?', (category,))
            else:
                self.cursor.execute('SELECT * FROM memory')
            
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting memories: {e}")
            return []
    
    def log_conversation(self, user_input: str, assistant_response: str, context: Dict = None) -> bool:
        if not self.enabled:
            return False
        
        try:
            context_json = json.dumps(context) if context else None
            self.cursor.execute('''
                INSERT INTO conversations (user_input, assistant_response, context)
                VALUES (?, ?, ?)
            ''', (user_input, assistant_response, context_json))
            self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Error logging conversation: {e}")
            return False
    
    def get_recent_conversations(self, limit: int = 10) -> List[Dict]:
        if not self.enabled:
            return []
        
        try:
            self.cursor.execute('''
                SELECT * FROM conversations
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting conversations: {e}")
            return []
    
    def create_event(self, title: str, start_time: str, end_time: str = None,
                    description: str = "", location: str = "", attendees: List[str] = None) -> int:
        if not self.enabled:
            return -1
        
        try:
            attendees_json = json.dumps(attendees) if attendees else None
            self.cursor.execute('''
                INSERT INTO events (title, description, start_time, end_time, location, attendees)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (title, description, start_time, end_time, location, attendees_json))
            self.connection.commit()
            return self.cursor.lastrowid
        except Exception as e:
            logger.error(f"Error creating event: {e}")
            return -1
    
    def get_events(self, start_date: str = None, end_date: str = None) -> List[Dict]:
        if not self.enabled:
            return []
        
        try:
            query = "SELECT * FROM events WHERE 1=1"
            params = []
            
            if start_date:
                query += " AND start_time >= ?"
                params.append(start_date)
            if end_date:
                query += " AND start_time <= ?"
                params.append(end_date)
            
            query += " ORDER BY start_time ASC"
            
            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting events: {e}")
            return []
    
    def index_file(self, path: str, filename: str, size: int, file_type: str,
                  category: str = None, tags: List[str] = None) -> bool:
        if not self.enabled:
            return False
        
        try:
            tags_json = json.dumps(tags) if tags else None
            modified_at = datetime.now().isoformat()
            
            self.cursor.execute('''
                INSERT OR REPLACE INTO files
                (path, filename, size, file_type, category, tags, modified_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (path, filename, size, file_type, category, tags_json, modified_at))
            self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Error indexing file: {e}")
            return False
    
    def search_files(self, query: str = None, category: str = None, file_type: str = None) -> List[Dict]:
        if not self.enabled:
            return []
        
        try:
            sql = "SELECT * FROM files WHERE 1=1"
            params = []
            
            if query:
                sql += " AND (filename LIKE ? OR tags LIKE ?)"
                params.extend([f'%{query}%', f'%{query}%'])
            if category:
                sql += " AND category = ?"
                params.append(category)
            if file_type:
                sql += " AND file_type = ?"
                params.append(file_type)
            
            sql += " ORDER BY modified_at DESC"
            
            self.cursor.execute(sql, params)
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error searching files: {e}")
            return []
    
    def create_automation_rule(self, name: str, trigger_type: str, trigger_params: Dict,
                              action_type: str, action_params: Dict) -> int:
        if not self.enabled:
            return -1
        
        try:
            self.cursor.execute('''
                INSERT INTO automation_rules
                (name, trigger_type, trigger_params, action_type, action_params)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, trigger_type, json.dumps(trigger_params),
                 action_type, json.dumps(action_params)))
            self.connection.commit()
            return self.cursor.lastrowid
        except Exception as e:
            logger.error(f"Error creating automation rule: {e}")
            return -1
    
    def get_automation_rules(self, enabled_only: bool = True) -> List[Dict]:
        if not self.enabled:
            return []
        
        try:
            if enabled_only:
                self.cursor.execute('SELECT * FROM automation_rules WHERE enabled = 1')
            else:
                self.cursor.execute('SELECT * FROM automation_rules')
            
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting automation rules: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        if not self.enabled:
            return {}
        
        try:
            stats = {}
            
            self.cursor.execute('SELECT COUNT(*) as count FROM tasks WHERE status = "pending"')
            stats['pending_tasks'] = self.cursor.fetchone()['count']
            
            self.cursor.execute('SELECT COUNT(*) as count FROM tasks WHERE status = "completed"')
            stats['completed_tasks'] = self.cursor.fetchone()['count']
            
            self.cursor.execute('SELECT COUNT(*) as count FROM memory')
            stats['memory_entries'] = self.cursor.fetchone()['count']
            
            self.cursor.execute('SELECT COUNT(*) as count FROM conversations')
            stats['total_conversations'] = self.cursor.fetchone()['count']
            
            self.cursor.execute('SELECT COUNT(*) as count FROM events')
            stats['total_events'] = self.cursor.fetchone()['count']
            
            self.cursor.execute('SELECT COUNT(*) as count FROM files')
            stats['indexed_files'] = self.cursor.fetchone()['count']
            
            return stats
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        if not self.enabled:
            return []
        
        try:
            self.cursor.execute(query, params)
            if query.strip().upper().startswith('SELECT'):
                rows = self.cursor.fetchall()
                return [dict(row) for row in rows]
            else:
                self.connection.commit()
                return [{'affected_rows': self.cursor.rowcount}]
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return []
    
    def close(self):
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")
    
    def __del__(self):
        self.close()

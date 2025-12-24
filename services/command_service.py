import re
import os
import subprocess
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class CommandService:
    """Service for parsing and executing user commands"""
    
    def __init__(self, phenom):
        self.phenom = phenom
    
    def parse_and_execute(self, message: str) -> Optional[Dict[str, Any]]:
        """
        Parse a message and execute the appropriate command
        Returns: dict with 'success' and 'response' keys, or None if not a command
        """
        original_message = message
        message = message.lower().strip()
        
        parsers = [
            self._parse_file_operations,
            self._parse_task_commands,
            self._parse_project_commands,
            self._parse_goal_commands,
            self._parse_note_commands,
            self._parse_habit_commands,
            self._parse_finance_commands,
            self._parse_journal_commands,
            self._parse_system_commands,
        ]
        
        for parser in parsers:
            result = parser(message, original_message)
            if result:
                return result
        
        return None
    
    def _parse_file_operations(self, message: str, original: str) -> Optional[Dict]:
        if re.search(r'(?:search|find|locate).{0,30}git\s*repo', message):
            return self._search_git_repos()
        
        match = re.search(r'(?:search|find|locate)\s+(?:file|files)\s+(.+)', message)
        if match:
            query = match.group(1).strip()
            return self._search_files(query)
        
        match = re.search(r'(?:search|google|look up|find)\s+(?:for|about)?\s*(.+)\s+(?:on|in)\s+(?:web|internet|google)', message)
        if match:
            query = match.group(1).strip()
            return self._web_search(query)
        
        return None
    
    def _parse_task_commands(self, message: str, original: str) -> Optional[Dict]:
        patterns = [
            r'(?:add|create|make|new)\s+(?:a\s+)?task\s+(?:called\s+|named\s+)?(.+)',
            r'(?:can\s+you\s+)?(?:add|create|make)\s+(?:a\s+)?task\s+(?:called\s+|named\s+|for\s+)?(.+)',
            r'(?:remind\s+me\s+to|i\s+need\s+to)\s+(.+)',
            r'task:\s*(.+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                task_title = match.group(1).strip()
                task_title = re.sub(r'\s+(please|thanks|thank you)$', '', task_title)
                return self._add_task(task_title)
        
        if re.search(r'(?:what|show|list|view|display|see).{0,30}(?:my\s+)?task', message) or message in ['tasks', 'my tasks']:
            return self._list_tasks()
        
        return None
    
    def _parse_project_commands(self, message: str, original: str) -> Optional[Dict]:
        patterns = [
            r'(?:add|create|start|new)\s+(?:a\s+)?project\s+(?:called\s+|named\s+)?(.+)',
            r'project:\s*(.+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                project_name = match.group(1).strip()
                return self._add_project(project_name)
        
        if re.search(r'(?:list|show|view|display|see).{0,30}project', message):
            return self._list_projects()
        
        return None
    
    def _parse_goal_commands(self, message: str, original: str) -> Optional[Dict]:
        patterns = [
            r'(?:add|create|set|new)\s+(?:a\s+)?goal\s+(?:called\s+|named\s+|to\s+)?(.+)',
            r'(?:i\s+want\s+to|my\s+goal\s+is\s+to)\s+(.+)',
            r'goal:\s*(.+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                goal_title = match.group(1).strip()
                return self._add_goal(goal_title)
        
        if re.search(r'(?:list|show|view|display|see).{0,30}goal', message):
            return self._list_goals()
        
        return None
    
    def _parse_note_commands(self, message: str, original: str) -> Optional[Dict]:
        patterns = [
            r'(?:add|create|write|make|new)\s+(?:a\s+)?note\s+(?:called\s+|titled\s+)?(.+)',
            r'(?:note|write)\s+down:?\s*(.+)',
            r'(?:save|remember)\s+this:?\s*(.+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                content = match.group(1).strip()
                return self._add_note(content)
        
        if re.search(r'(?:list|show|view|display|see).{0,30}note', message):
            return self._list_notes()
        
        return None
    
    def _parse_habit_commands(self, message: str, original: str) -> Optional[Dict]:
        patterns = [
            r'(?:add|create|track|start)\s+(?:a\s+)?habit\s+(?:called\s+|named\s+)?(.+)',
            r'(?:i\s+want\s+to\s+)?track\s+(.+)\s+(?:habit|daily|weekly)',
        ]
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                habit_name = match.group(1).strip()
                return self._add_habit(habit_name)
        
        if re.search(r'(?:list|show|view|display|see).{0,30}habit', message):
            return self._list_habits()
        
        return None
    
    def _parse_finance_commands(self, message: str, original: str) -> Optional[Dict]:
        patterns = [
            r'(?:add|record|log)\s+(?:an\s+)?expense\s+(?:of\s+)?(\d+\.?\d*)\s+(?:for|on)\s+(.+)',
            r'spent\s+(\d+\.?\d*)\s+on\s+(.+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                amount = float(match.group(1))
                category = match.group(2).strip()
                return self._add_expense(amount, category)
        
        if re.search(r'(?:financial|finance|money)\s+(?:summary|overview|status)', message):
            return self._get_financial_summary()
        
        return None
    
    def _parse_journal_commands(self, message: str, original: str) -> Optional[Dict]:
        patterns = [
            r'(?:add|create|write)\s+(?:a\s+)?journal\s+entry:?\s*(.+)',
            r'journal:\s*(.+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                entry = match.group(1).strip()
                return self._add_journal_entry(entry)
        
        return None
    
    def _parse_system_commands(self, message: str, original: str) -> Optional[Dict]:
        if re.search(r'(?:what\s+can\s+you\s+do|help|capabilities|commands)', message):
            return self._get_capabilities()
        
        if re.search(r'(?:system\s+status|system\s+info|(?:show|check|what|get|display|tell me).{0,30}(?:system|cpu|memory|ram|disk|gpu|resource))', message):
            return self._get_system_status()
        
        return None
    
    def _search_git_repos(self) -> Dict:
        try:
            result = subprocess.run(
                ['find', os.path.expanduser('~'), '-type', 'd', '-name', '.git', '-prune'],
                capture_output=True, text=True, timeout=10
            )
            repos = [line.replace('/.git', '') for line in result.stdout.strip().split('\n') if line][:10]
            if repos:
                repo_list = '\n'.join([f"• {repo}" for repo in repos])
                return {"success": True, "response": f"Found {len(repos)} git repositories:\n{repo_list}"}
            return {"success": True, "response": "No git repositories found."}
        except Exception as e:
            logger.error(f"Git repo search error: {e}")
            return {"success": True, "response": "Search completed with limited results."}
    
    def _search_files(self, query: str) -> Dict:
        try:
            results = self.phenom.file_search.search(query, max_results=10)
            if results:
                file_list = '\n'.join([f"• {r}" for r in results[:10]])
                return {"success": True, "response": f"Files matching '{query}':\n{file_list}"}
            return {"success": True, "response": f"No files found matching '{query}'."}
        except Exception as e:
            logger.error(f"File search error: {e}")
            return {"success": True, "response": "File search feature requires configuration."}
    
    def _web_search(self, query: str) -> Dict:
        try:
            results = self.phenom.web.search(query, max_results=5)
            if results:
                result_list = '\n'.join([f"• {r.get('title', 'Result')}: {r.get('url', '')}" for r in results[:5]])
                return {"success": True, "response": f"Web search results for '{query}':\n{result_list}"}
        except Exception as e:
            logger.error(f"Web search error: {e}")
        return {"success": True, "response": f"Web search requires configuration. Try searching manually for: {query}"}
    
    def _add_task(self, title: str) -> Dict:
        task = self.phenom.tasks.add_task(title, priority="medium")
        return {"success": True, "response": f"✓ Task '{title}' added successfully!"}
    
    def _list_tasks(self) -> Dict:
        tasks = self.phenom.tasks.get_pending_tasks()
        if not tasks:
            return {"success": True, "response": "No pending tasks."}
        task_list = "\n".join([f"• {t['title']} ({t['priority']} priority)" for t in tasks[:10]])
        return {"success": True, "response": f"Pending tasks:\n{task_list}"}
    
    def _add_project(self, name: str) -> Dict:
        project = self.phenom.project_manager.create_project(name)
        return {"success": True, "response": f"✓ Project '{name}' created successfully!"}
    
    def _list_projects(self) -> Dict:
        projects = self.phenom.project_manager.list_projects()
        if not projects:
            return {"success": True, "response": "No active projects."}
        proj_list = "\n".join([f"• {p['name']}" for p in projects[:10]])
        return {"success": True, "response": f"Active projects:\n{proj_list}"}
    
    def _add_goal(self, title: str) -> Dict:
        goal = self.phenom.goal_tracker.add_goal(title)
        return {"success": True, "response": f"✓ Goal '{title}' added successfully!"}
    
    def _list_goals(self) -> Dict:
        goals = self.phenom.goal_tracker.get_all_goals()
        if not goals:
            return {"success": True, "response": "No goals set."}
        goal_list = "\n".join([f"• {g['title']} (Progress: {g.get('progress', 0)}%)" for g in goals[:10]])
        return {"success": True, "response": f"Your goals:\n{goal_list}"}
    
    def _add_note(self, content: str) -> Dict:
        note = self.phenom.notes_manager.add_note("Quick Note", content)
        return {"success": True, "response": "✓ Note saved!"}
    
    def _list_notes(self) -> Dict:
        notes = self.phenom.notes_manager.list_notes()[:10]
        if not notes:
            return {"success": True, "response": "No notes found."}
        note_list = "\n".join([f"• {n.get('title', 'Untitled')}" for n in notes])
        return {"success": True, "response": f"Your notes:\n{note_list}"}
    
    def _add_habit(self, name: str) -> Dict:
        habit = self.phenom.habit_tracker.create_habit(name, frequency='daily')
        return {"success": True, "response": f"✓ Habit '{name}' created! Track it daily."}
    
    def _list_habits(self) -> Dict:
        habits = self.phenom.habit_tracker.list_habits()[:10]
        if not habits:
            return {"success": True, "response": "No habits tracked."}
        habit_list = "\n".join([f"• {h.get('name', 'Habit')}" for h in habits])
        return {"success": True, "response": f"Your habits:\n{habit_list}"}
    
    def _add_expense(self, amount: float, category: str) -> Dict:
        self.phenom.finance_tracker.add_expense(amount, category)
        return {"success": True, "response": f"✓ Expense of ${amount} recorded for {category}"}
    
    def _get_financial_summary(self) -> Dict:
        try:
            summary = self.phenom.finance_tracker.get_summary()
            return {"success": True, "response": f"Financial Summary:\n{summary}"}
        except Exception as e:
            logger.error(f"Financial summary error: {e}")
            return {"success": True, "response": "Financial tracking feature requires configuration."}
    
    def _add_journal_entry(self, entry: str) -> Dict:
        self.phenom.journal.add_entry(entry)
        return {"success": True, "response": "✓ Journal entry added!"}
    
    def _get_capabilities(self) -> Dict:
        capabilities = """
I can help you with:

📋 **Task Management**
- Add, list, complete tasks
- Set priorities and deadlines

🎯 **Goals & Projects**
- Create and track goals
- Manage projects
- Track progress

📝 **Notes & Journal**
- Quick notes
- Journal entries
- Search notes

💪 **Habits & Health**
- Track daily habits
- Log health metrics

💰 **Finance**
- Track expenses
- Financial summaries

🔍 **Search**
- Find files on your PC
- Search git repositories
- Web search (when configured)

Just ask naturally! Example: "remind me to call john" or "add expense 50 for groceries"
"""
        return {"success": True, "response": capabilities}
    
    def _get_system_status(self) -> Dict:
        try:
            from services.system_service import SystemService
            system_service = SystemService(self.phenom)
            status = system_service.get_system_status()
            
            cpu = status.get('cpu', {})
            memory = status.get('memory', {})
            disk = status.get('disk', {})
            gpu = status.get('gpu', {})
            ai = status.get('ai', {})
            
            response = "📊 **System Status**\n\n"
            
            if cpu and 'error' not in cpu:
                response += f"⚡ **CPU**: {cpu.get('usage_percent', 0):.1f}% usage "
                response += f"({cpu.get('cores', 'N/A')} cores, {cpu.get('threads', 'N/A')} threads)\n"
            
            if memory and 'error' not in memory:
                response += f"💾 **Memory**: {memory.get('used_gb', 0):.1f}GB / {memory.get('total_gb', 0):.1f}GB "
                response += f"({memory.get('percent', 0):.1f}% used)\n"
            
            if disk and 'error' not in disk:
                response += f"💿 **Disk**: {disk.get('used_gb', 0):.1f}GB / {disk.get('total_gb', 0):.1f}GB "
                response += f"({disk.get('percent', 0):.1f}% used)\n"
            
            if gpu and 'error' not in gpu:
                if gpu.get('available'):
                    response += f"🎮 **GPU**: {gpu.get('type', 'Unknown')} - {gpu.get('name', 'N/A')}\n"
                else:
                    response += "🎮 **GPU**: Not detected\n"
            
            if ai and 'error' not in ai:
                response += f"\n🤖 **AI System**\n"
                response += f"- Mode: {ai.get('mode', 'Unknown')}\n"
                response += f"- Local LLM: {'✓ Online' if ai.get('local_available') else '✗ Offline'}\n"
                response += f"- Cloud LLM: {'✓ Online' if ai.get('cloud_available') else '✗ Offline'}\n"
            
            return {"success": True, "response": response}
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {"success": True, "response": "Unable to retrieve system status. Please try again."}

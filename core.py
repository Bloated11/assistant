import logging
import yaml
import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv(override=True)

console_log_level = os.getenv('LOG_LEVEL', 'ERROR')
console_handler = logging.StreamHandler()
console_handler.setLevel(getattr(logging, console_log_level))
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logging.basicConfig(
    level=logging.DEBUG,
    handlers=[console_handler]
)


from modules.automation import AutomationManager
from modules.web_search import WebManager
from modules.file_search import FileSearchEngine
from modules.tasks import TaskManager
from modules.ai import AIManager
from modules.learning import LearningManager
# UNUSED: Commented out to improve startup time and reduce memory footprint
# from modules.notifications import NotificationManager
# from modules.personality import PersonalityEngine
from modules.database import DatabaseManager
# from modules.nlp import NLPManager
from modules.vector_db import VectorDBManager  # RAGManager removed (unused)
# from modules.knowledge_graph import KnowledgeGraphManager
# from modules.productivity import PomodoroManager, FocusModeManager
from modules.project_management import ProjectManager
from modules.habits import HabitTracker
from modules.notes import NotesManager
from modules.finance import FinanceTracker
from modules.goals import GoalTracker
from modules.health import HealthTracker
from modules.reading import ReadingListManager
from modules.meals import MealPlanner
from modules.learning_tracker import LearningTrackerModule
from modules.time_tracker import TimeTracker
from modules.journal import JournalSystem
from modules.contacts import ContactManager as ContactsManager
from modules.travel import TravelPlanner
from modules.reminders import ReminderSystem
from modules.ideas import IdeaTracker
from modules.inventory import InventoryManager
from modules.quotes import QuoteCollection
from modules.events import EventTracker
from modules.archive import ArchiveManager
from modules.voice import VoiceManager

logger = logging.getLogger(__name__)

class Phenom:
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config = self._load_config(config_path)
        self.name = self.config.get('phenom', {}).get('name', 'Phenom')
        self.wake_word = self.config.get('phenom', {}).get('wake_word', 'phenom')
        
        self._setup_logging()
        
        logger.info(f"Initializing {self.name}...")
        
        self.automation = AutomationManager(self.config.get('automation', {}))
        self.web = WebManager(self.config.get('web_search', {}))
        self.file_search = FileSearchEngine(self.config.get('file_search', {}))
        self.tasks = TaskManager(self.config.get('tasks', {}))
        self.ai = AIManager(self.config.get('ai', {}))
        self.learning = LearningManager(self.config.get('learning', {}))
        
        # After learning and AI are initialized, import any configured personal env vars into memory
        try:
            self._import_personal_envs()
        except Exception as e:
            logger.error(f"Error importing personal envs: {e}")
        
        # UNUSED MODULES: Commented out to reduce startup time (~400ms) and memory (1.6MB)
        # Uncomment when features are implemented in web routes
        # self.notifications = NotificationManager(self.config.get('notifications', {}))
        # self.personality = PersonalityEngine(self.config.get('personality', {}))
        self.database = DatabaseManager(self.config.get('database', {}))
        # self.nlp = NLPManager(self.config.get('nlp', {}))
        
        self.vector_db = VectorDBManager(self.config.get('vector_db', {}))
        # self.rag = RAGManager(self.vector_db, self.ai)
        # self.knowledge_graph = KnowledgeGraphManager(self.config.get('knowledge_graph', {}))
        
        # self.pomodoro = PomodoroManager(self.config.get('pomodoro', {}))
        # self.focus_mode = FocusModeManager(self.config.get('focus_mode', {}))
        self.project_manager = ProjectManager(self.config.get('project_management', {}))
        self.habit_tracker = HabitTracker(self.config.get('habits', {}))
        self.notes_manager = NotesManager(self.config.get('notes', {}))
        self.finance_tracker = FinanceTracker(self.config.get('finance', {}))
        self.goal_tracker = GoalTracker(self.config.get('goals', {}))
        self.health_tracker = HealthTracker(self.config.get('health', {}))
        self.reading_list = ReadingListManager(self.config.get('reading', {}))
        self.meal_planner = MealPlanner(self.config.get('meals', {}))
        self.learning_tracker = LearningTrackerModule(self.config.get('learning_tracker', {}))
        self.time_tracker = TimeTracker(self.config.get('time_tracker', {}))
        self.journal = JournalSystem(self.config.get('journal', {}))
        self.contact_manager = ContactsManager(self.config.get('contacts', {}))
        self.travel_planner = TravelPlanner(self.config.get('travel', {}))
        self.reminder_system = ReminderSystem(self.config.get('reminders', {}))
        self.idea_tracker = IdeaTracker(self.config.get('ideas', {}))
        self.inventory_manager = InventoryManager(self.config.get('inventory', {}))
        self.quote_collection = QuoteCollection(self.config.get('quotes', {}))
        self.event_tracker = EventTracker(self.config.get('events', {}))
        self.archive_manager = ArchiveManager(self.config.get('archive', {}))
        self.voice = VoiceManager(self.config.get('voice', {}))
        
        self.command_processor = None
        
        logger.info(f"{self.name} initialized successfully")
    
    def _load_config(self, config_path: str) -> dict:
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}
    
    def _setup_logging(self):
        from logging.handlers import RotatingFileHandler
        
        log_config = self.config.get('logs', {})
        file_log_level = log_config.get('level', 'INFO')
        log_file = log_config.get('file', 'logs/phenom.log')
        max_bytes = log_config.get('max_bytes', 10485760)
        backup_count = log_config.get('backup_count', 3)
        
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(getattr(logging, file_log_level))
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        
        root_logger = logging.getLogger()
        root_logger.addHandler(file_handler)
    
    def _is_enabled(self, attr_name: str) -> bool:
        """Return True if the given manager attribute exists and is enabled."""
        obj = getattr(self, attr_name, None)
        return getattr(obj, 'enabled', False)

    def _import_personal_envs(self):
        """Persist selected personal env vars into learning memory (opt-in).

        Behaviour:
        - If `ai.personal_injection.enabled` is False -> do nothing
        - If `ai.personal_injection.env_keys` is provided, use those env vars
        - Otherwise, collect all env vars starting with `PHENOM_`
        - Only write a fact if it does not already exist in memory
        """
        ai_conf = self.config.get('ai', {}).get('personal_injection', {})
        enabled = ai_conf.get('enabled', False)
        if not enabled:
            return

        keys = ai_conf.get('env_keys', [])
        collected = {}

        if keys:
            for k in keys:
                v = os.getenv(k)
                if v:
                    collected[k] = v
        else:
            for k, v in os.environ.items():
                if k.startswith('PHENOM_') and v:
                    collected[k] = v

        if not collected:
            logger.debug('No personal env vars found to import')
            return

        # Remember facts only if not already present
        for k, v in collected.items():
            existing = self.learning.recall_fact(k)
            if existing is None:
                self.learning.remember_fact(k, v)
                logger.info(f"Imported personal env var into memory: {k}")
            else:
                logger.debug(f"Personal env var {k} already present in memory; skipping")

    def process_command(self, command: str) -> str:
        if not self.command_processor:
            from command_processor import CommandProcessor
            self.command_processor = CommandProcessor(self)
        
        return self.command_processor.process(command)
    
    def run_voice_mode(self):
        if not self.voice.is_available():
            logger.warning("Voice mode is not available")
            print("Voice mode is not enabled. Please use text mode instead.")
            print("To enable voice mode, install required dependencies:")
            print("  pip install pyttsx3 SpeechRecognition PyAudio")
            self.run_text_mode()
            return
        
        logger.info("Starting voice mode...")
        print(f"\n{self.name} Voice Mode")
        print("=" * 50)
        print(f"Say '{self.wake_word}' to activate, then speak your command")
        print("Say 'exit' or 'quit' to stop")
        print("\nTIP: Speak clearly and loudly. Wait for the beep or 'Yes?' response.")
        print("=" * 50)
        print()
        
        self.voice.list_microphones()
        self.voice.speak(f"{self.name} voice mode activated. Say {self.wake_word} to give commands.")
        
        while True:
            try:
                print(f"\n{'='*50}")
                print(f"🔍 Waiting for wake word '{self.wake_word}' (speak now)...")
                print(f"{'='*50}")
                
                if self.voice.listen_for_wake_word(timeout=30, show_feedback=True):
                    self.voice.speak("Yes?")
                    print(f"\n{self.name}: Yes? What can I do for you?")
                    print("Speak your command now...")
                    
                    command = self.voice.listen(timeout=10, show_feedback=True)
                    
                    if not command:
                        self.voice.speak("I didn't catch that. Please try again.")
                        continue
                    
                    print(f"\nYou: {command}")
                    
                    if command.lower() in ['exit', 'quit', 'goodbye', 'stop']:
                        self.voice.speak("Goodbye!")
                        print(f"{self.name}: Shutting down.")
                        break
                    
                    print(f"{self.name}: Processing your request...")
                    response = self.ai.generate(command)
                    
                    if response:
                        print(f"{self.name}: {response}")
                        self.voice.speak(response)
                    else:
                        self.voice.speak("I'm having trouble processing that request.")
                
            except KeyboardInterrupt:
                print("\nShutting down voice mode...")
                self.voice.speak("Goodbye!")
                break
            except Exception as e:
                logger.error(f"Voice mode error: {e}")
                print(f"Error: {e}")
    
    def run_text_mode(self):
        logger.info("Starting text mode...")
        print(f"\n{self.name} Text Mode")
        print("=" * 50)
        print(f"💬 Chat naturally or use commands (type 'help' for list)")
        print(f"🚪 Type 'exit' or 'quit' to stop")
        print("=" * 50)
        print()
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    print(f"{self.name}: Goodbye!")
                    break
                
                response = self.process_command(user_input)
                print(f"{self.name}: {response}\n")
                
            except KeyboardInterrupt:
                print(f"\n{self.name}: Goodbye!")
                break
            except Exception as e:
                logger.error(f"Error in text mode: {e}")
                print(f"{self.name}: I encountered an error. Please try again.")
    
    def run_hybrid_mode(self):
        logger.info("Starting hybrid mode...")
        print(f"\n{self.name} Hybrid Mode")
        print("=" * 50)
        print("Commands:")
        print("  'voice' - Switch to voice mode")
        print("  'text'  - Switch to text mode")
        print("  'exit'  - Quit Phenom")
        print("=" * 50)
        
        while True:
            try:
                mode = input("\nSelect mode (voice/text/exit): ").strip().lower()
                
                if mode == 'voice':
                    self.run_voice_mode()
                elif mode == 'text':
                    self.run_text_mode()
                elif mode in ['exit', 'quit']:
                    print(f"{self.name}: Shutting down. Goodbye!")
                    break
                else:
                    print("Invalid mode. Please choose 'voice', 'text', or 'exit'.")
                    
            except KeyboardInterrupt:
                print(f"\n{self.name}: Shutting down. Goodbye!")
                break
    
    def get_status(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'ai_mode': self.ai.mode,
            'local_ai_available': self.ai.is_local_available(),
            'cloud_ai_available': self.ai.is_cloud_available(),
            'modules': {
                'automation': self._is_enabled('automation'),
                'web_search': self._is_enabled('web'),
                'tasks': self._is_enabled('tasks'),
                'learning': self._is_enabled('learning'),
                'notifications': self._is_enabled('notifications'),
                'personality': self._is_enabled('personality'),
                'database': self._is_enabled('database'),
                'nlp': self._is_enabled('nlp'),
                'vector_db': self._is_enabled('vector_db'),
                'rag': self._is_enabled('rag'),
                'knowledge_graph': self._is_enabled('knowledge_graph'),
                'pomodoro': self._is_enabled('pomodoro'),
                'focus_mode': self._is_enabled('focus_mode'),
                'project_management': self._is_enabled('project_manager'),
                'habits': self._is_enabled('habit_tracker'),
                'notes': self._is_enabled('notes_manager'),
                'finance': self._is_enabled('finance_tracker'),
                'goals': self._is_enabled('goal_tracker'),
                'health': self._is_enabled('health_tracker'),
                'reading': self._is_enabled('reading_list'),
                'meals': self._is_enabled('meal_planner'),
                'learning_tracker': self._is_enabled('learning_tracker'),
                'time_tracker': self._is_enabled('time_tracker'),
                'password_manager': self._is_enabled('password_manager'),
                'journal': self._is_enabled('journal'),
                'contacts': self._is_enabled('contact_manager'),
                'travel': self._is_enabled('travel_planner'),
                'reminders': self._is_enabled('reminder_system'),
                'ideas': self._is_enabled('idea_tracker'),
                'workout_routines': self._is_enabled('workout_routines'),
                'subscriptions': self._is_enabled('subscription_tracker'),
                'inventory': self._is_enabled('inventory_manager'),
                'quotes': self._is_enabled('quote_collection'),
                'events': self._is_enabled('event_tracker'),
                'archive': self._is_enabled('archive_manager')
            },
            'task_summary': self.tasks.get_task_summary(),
            'user_profile': self.learning.get_user_profile()
        }

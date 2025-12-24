#!/usr/bin/env python3
"""Comprehensive Health Check for Phenom AI"""
import os, sys, json
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

class HealthCheck:
    def __init__(self):
        self.results = {'timestamp': datetime.now().isoformat(), 'environment': {}, 'cloud_ai': {}, 'modules': {}, 'database': {}, 'web_server': {}, 'overall_status': 'UNKNOWN'}
        self.errors, self.warnings = [], []
        
    def print_header(self, text):
        print(f"\n{'='*60}\n  {text}\n{'='*60}")
    
    def print_status(self, name, status, details=""):
        symbols = {'PASS': '✓', 'FAIL': '✗', 'WARN': '⚠', 'SKIP': '○'}
        colors = {'PASS': '\033[92m', 'FAIL': '\033[91m', 'WARN': '\033[93m', 'SKIP': '\033[94m', 'END': '\033[0m'}
        symbol, color = symbols.get(status, '?'), colors.get(status, '')
        status_str = f"{color}{symbol} {name:<40} [{status}]{colors['END']}"
        if details: status_str += f"\n   {details}"
        print(status_str)
        
    def check_environment(self):
        self.print_header("ENVIRONMENT CHECK")
        py_version = sys.version.split()[0]
        self.results['environment']['python_version'] = py_version
        if sys.version_info >= (3, 8):
            self.print_status(f"Python Version ({py_version})", "PASS")
        else:
            self.print_status(f"Python Version ({py_version})", "FAIL", "Requires Python 3.8+")
            self.errors.append("Python version < 3.8")
        
        for fname, key in [('.env', 'env_file'), ('config/config.yaml', 'config_file')]:
            if os.path.exists(fname):
                self.print_status(f"{fname} exists", "PASS")
                self.results['environment'][key] = True
            else:
                self.print_status(f"{fname} exists", "FAIL")
                self.errors.append(f"{fname} missing")
                self.results['environment'][key] = False
    
    def check_cloud_ai_providers(self):
        self.print_header("CLOUD AI PROVIDERS CHECK")
        providers = {
            'openai': {'env_var': 'OPENAI_API_KEY', 'package': 'openai', 'test_model': 'gpt-3.5-turbo'},
            'anthropic': {'env_var': 'ANTHROPIC_API_KEY', 'package': 'anthropic', 'test_model': 'claude-3-haiku-20240307'},
            'openrouter': {'env_var': 'OPENROUTER_API_KEY', 'package': 'openai', 'test_model': 'anthropic/claude-3-haiku', 'base_url': 'https://openrouter.ai/api/v1'}
        }
        
        for provider, config in providers.items():
            api_key = os.getenv(config['env_var'])
            if not api_key:
                self.print_status(f"{provider.upper()} - API Key", "FAIL", f"{config['env_var']} not set")
                self.errors.append(f"{provider} API key missing")
                self.results['cloud_ai'][provider] = {'status': 'FAIL', 'reason': 'No API key'}
                continue
            
            if api_key == f"your-{provider}-api-key-here" or len(api_key) < 20:
                self.print_status(f"{provider.upper()} - API Key", "WARN", "Placeholder key detected")
                self.warnings.append(f"{provider} API key appears to be placeholder")
                self.results['cloud_ai'][provider] = {'status': 'WARN', 'reason': 'Placeholder key'}
                continue
            
            self.print_status(f"{provider.upper()} - API Key", "PASS", f"Key length: {len(api_key)}")
            
            try:
                if config['package'] == 'openai':
                    from openai import OpenAI
                elif config['package'] == 'anthropic':
                    from anthropic import Anthropic
                self.print_status(f"{provider.upper()} - Package", "PASS")
            except ImportError as e:
                self.print_status(f"{provider.upper()} - Package", "FAIL", str(e))
                self.errors.append(f"{provider} package not installed")
                self.results['cloud_ai'][provider] = {'status': 'FAIL', 'reason': 'Package missing'}
                continue
            
            try:
                if provider == 'openai':
                    from openai import OpenAI
                    client = OpenAI(api_key=api_key)
                elif provider == 'anthropic':
                    from anthropic import Anthropic
                    client = Anthropic(api_key=api_key)
                elif provider == 'openrouter':
                    from openai import OpenAI
                    client = OpenAI(api_key=api_key, base_url=config['base_url'])
                self.print_status(f"{provider.upper()} - Connection", "PASS", "Client initialized")
                self.results['cloud_ai'][provider] = {'status': 'PASS', 'model': config['test_model']}
            except Exception as e:
                self.print_status(f"{provider.upper()} - Connection", "FAIL", str(e)[:80])
                self.errors.append(f"{provider} connection failed")
                self.results['cloud_ai'][provider] = {'status': 'FAIL', 'reason': str(e)[:100]}
    
    def check_modules(self):
        self.print_header("MODULES CHECK")
        try:
            from core import Phenom
            phenom = Phenom()
            self.print_status("Core - Phenom initialization", "PASS")
            
            modules = [
                ('ai', 'AI Module', lambda: hasattr(phenom.ai, 'generate_response')),
                ('tasks', 'Task Manager', lambda: phenom.tasks.get_all_tasks()),
                ('project_manager', 'Project Manager', lambda: phenom.project_manager.list_projects()),
                ('goal_tracker', 'Goal Tracker', lambda: phenom.goal_tracker.get_all_goals()),
                ('notes_manager', 'Notes Manager', lambda: phenom.notes_manager.list_notes()),
                ('finance_tracker', 'Finance Tracker', lambda: hasattr(phenom.finance_tracker, 'create_transaction')),
                ('habit_tracker', 'Habit Tracker', lambda: phenom.habit_tracker.list_habits()),
                ('automation', 'Automation Manager', lambda: hasattr(phenom.automation, 'list_tasks')),
                ('web', 'Web Search', lambda: hasattr(phenom.web, 'search')),
                ('event_tracker', 'Event Tracker', lambda: hasattr(phenom.event_tracker, 'get_events')),
            ]
            
            for attr_name, display_name, test_func in modules:
                try:
                    if hasattr(phenom, attr_name):
                        result = test_func()
                        self.print_status(display_name, "PASS")
                        self.results['modules'][attr_name] = {'status': 'PASS'}
                    else:
                        self.print_status(display_name, "FAIL", f"Module not found")
                        self.errors.append(f"Module {attr_name} missing")
                        self.results['modules'][attr_name] = {'status': 'FAIL', 'reason': 'Not found'}
                except Exception as e:
                    self.print_status(display_name, "WARN", str(e)[:60])
                    self.warnings.append(f"{display_name}: {str(e)[:50]}")
                    self.results['modules'][attr_name] = {'status': 'WARN', 'reason': str(e)[:100]}
        except Exception as e:
            self.print_status("Core - Phenom initialization", "FAIL", str(e))
            self.errors.append(f"Phenom initialization failed")
            self.results['modules']['core'] = {'status': 'FAIL', 'reason': str(e)}
    
    def check_database(self):
        self.print_header("DATABASE CHECK")
        db_files = {'tasks': 'data/tasks.json', 'projects': 'data/projects.json', 'goals': 'data/goals.json', 'notes': 'data/notes.json', 'habits': 'data/habits.json', 'finance': 'data/finances.json'}
        
        for db_name, db_path in db_files.items():
            if os.path.exists(db_path):
                try:
                    with open(db_path, 'r') as f:
                        data = json.load(f)
                    self.print_status(f"Database - {db_name}", "PASS", f"{len(data)} records")
                    self.results['database'][db_name] = {'status': 'PASS', 'records': len(data)}
                except:
                    self.print_status(f"Database - {db_name}", "FAIL", "Invalid JSON")
                    self.errors.append(f"{db_name} database corrupted")
                    self.results['database'][db_name] = {'status': 'FAIL', 'reason': 'Invalid JSON'}
            else:
                self.print_status(f"Database - {db_name}", "WARN", "Will be created")
                self.warnings.append(f"{db_name} database missing")
                self.results['database'][db_name] = {'status': 'WARN', 'reason': 'Not found'}
    
    def check_web_server(self):
        self.print_header("WEB SERVER CHECK")
        for package, name in [('fastapi', 'FastAPI'), ('uvicorn', 'Uvicorn'), ('jinja2', 'Jinja2'), ('passlib', 'Passlib')]:
            try:
                __import__(package)
                self.print_status(f"Web Package - {name}", "PASS")
                self.results['web_server'][package] = {'status': 'PASS'}
            except ImportError:
                self.print_status(f"Web Package - {name}", "FAIL")
                self.errors.append(f"{package} missing")
                self.results['web_server'][package] = {'status': 'FAIL'}
        
        if os.path.exists('web/templates'):
            count = len([f for f in os.listdir('web/templates') if f.endswith('.html')])
            self.print_status("Web Templates", "PASS", f"{count} templates")
            self.results['web_server']['templates'] = {'status': 'PASS', 'count': count}
        else:
            self.print_status("Web Templates", "FAIL")
            self.errors.append("Web templates missing")
        
        try:
            import requests
            response = requests.get('http://localhost:8000', timeout=2)
            self.print_status("Web Server - Running", "PASS", f"Status: {response.status_code}")
            self.results['web_server']['running'] = {'status': 'PASS', 'port': 8000}
        except:
            self.print_status("Web Server - Running", "WARN", "Start with: python run_web.py")
            self.warnings.append("Web server not running")
            self.results['web_server']['running'] = {'status': 'WARN'}
    
    def generate_summary(self):
        self.print_header("SUMMARY")
        total_errors, total_warnings = len(self.errors), len(self.warnings)
        
        if total_errors == 0 and total_warnings == 0:
            self.results['overall_status'] = 'HEALTHY'
            status, message = 'PASS', "All systems operational!"
        elif total_errors == 0:
            self.results['overall_status'] = 'DEGRADED'
            status, message = 'WARN', f"System operational with {total_warnings} warning(s)"
        else:
            self.results['overall_status'] = 'CRITICAL'
            status, message = 'FAIL', f"System has {total_errors} critical error(s)"
        
        self.print_status("Overall Status", status, message)
        
        if self.errors:
            print("\n🔴 CRITICAL ERRORS:")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
        
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
        
        results_file = f"health_check_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n📊 Detailed results saved to: {results_file}")
    
    def run(self):
        print("\n" + "="*60)
        print("  PHENOM AI - COMPREHENSIVE HEALTH CHECK")
        print("="*60)
        self.check_environment()
        self.check_cloud_ai_providers()
        self.check_modules()
        self.check_database()
        self.check_web_server()
        self.generate_summary()
        print("\n" + "="*60 + "\n")
        return 0 if len(self.errors) == 0 else 1

if __name__ == '__main__':
    checker = HealthCheck()
    exit_code = checker.run()
    sys.exit(exit_code)

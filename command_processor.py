import json
import logging

logger = logging.getLogger(__name__)

class CommandProcessor:
    def __init__(self, phenom):
        self.phenom = phenom

    def process(self, command: str) -> str:
        cmd = command.strip()
        if not cmd:
            return ""
        
        cmd_lower = cmd.lower()
        
        if cmd_lower in ('help', '?'):
            return "Available commands: help, status, quit, exit\nOr just chat with me naturally!"
        if cmd_lower in ('quit', 'exit'):
            return "Goodbye!"
        if cmd_lower == 'status':
            try:
                return json.dumps(self.phenom.get_status(), indent=2)
            except Exception as e:
                logger.exception("Error while getting status")
                return "Unable to get status."
        if cmd.startswith('pip install'):
            return "Package installation must be done outside Phenom (use your shell)."
        
        try:
            response = self.phenom.ai.generate(cmd)
            return response if response else "I'm having trouble processing that right now."
        except Exception as e:
            logger.error(f"AI generation error: {e}")
            return "I encountered an error processing your message."
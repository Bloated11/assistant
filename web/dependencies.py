from typing import Generator
from fastapi import Depends
from sqlalchemy.orm import Session
from web.database import get_db
from core import Phenom
from services import CommandService, AIService, SystemService

_phenom_instance = None
_command_service_instance = None
_ai_service_instance = None
_system_service_instance = None

def get_phenom() -> Phenom:
    """Dependency provider for Phenom core instance"""
    global _phenom_instance
    if _phenom_instance is None:
        _phenom_instance = Phenom()
    return _phenom_instance

def get_command_service(phenom: Phenom = Depends(get_phenom)) -> CommandService:
    """Dependency provider for CommandService"""
    global _command_service_instance
    if _command_service_instance is None:
        _command_service_instance = CommandService(phenom)
    return _command_service_instance

def get_ai_service(phenom: Phenom = Depends(get_phenom)) -> AIService:
    """Dependency provider for AIService"""
    global _ai_service_instance
    if _ai_service_instance is None:
        _ai_service_instance = AIService(phenom)
    return _ai_service_instance

def get_system_service(phenom: Phenom = Depends(get_phenom)) -> SystemService:
    """Dependency provider for SystemService"""
    global _system_service_instance
    if _system_service_instance is None:
        _system_service_instance = SystemService(phenom)
    return _system_service_instance

def get_db_session() -> Generator[Session, None, None]:
    """Dependency provider for database sessions"""
    return get_db()

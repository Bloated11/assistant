import pytest
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ['AI_MODE'] = 'local'
os.environ['TESTING'] = '1'

@pytest.fixture
def test_config():
    return {
        'ai': {
            'mode': 'local',
            'local': {
                'enabled': True,
                'model': 'phi3:mini',
                'base_url': 'http://localhost:11434',
                'temperature': 0.7,
                'timeout': 30
            },
            'cloud': {
                'enabled': False,
                'provider': 'openai'
            }
        },
        'voice': {
            'enabled': False
        },
        'phenom': {
            'name': 'phenom',
            'wake_word': 'phenom'
        }
    }

@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv('AI_MODE', 'local')
    monkeypatch.setenv('OPENAI_API_KEY', 'test-key-123')
    monkeypatch.setenv('DATABASE_PATH', ':memory:')
    monkeypatch.setenv('TESTING', '1')

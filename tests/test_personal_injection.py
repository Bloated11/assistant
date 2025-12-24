import os
import tempfile
import yaml
from core import Phenom


def test_imports_personal_env_to_memory(monkeypatch, tmp_path):
    monkeypatch.setenv('PHENOM_AGE', '50')

    cfg = {
        'ai': {
            'mode': 'local',
            'local': {'enabled': False},
            'personal_injection': {'enabled': True, 'env_keys': []}
        },
        'learning': {
            'memory_file': str(tmp_path / 'memory.json'),
            'conversation_history': str(tmp_path / 'convos.json')
        }
    }

    cfg_file = tmp_path / 'cfg.yaml'
    with open(cfg_file, 'w') as f:
        yaml.safe_dump(cfg, f)

    phenom = Phenom(config_path=str(cfg_file))

    assert phenom.learning.recall_fact('PHENOM_AGE') == '50'

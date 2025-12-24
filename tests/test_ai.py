import pytest
from unittest.mock import Mock, patch, MagicMock
from modules.ai.ai_manager import AIManager
from modules.ai.local_llm import LocalLLM
from modules.ai.cloud_llm import CloudLLM

@pytest.fixture
def local_config():
    return {
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
    }

@pytest.fixture
def cloud_config():
    return {
        'mode': 'cloud',
        'local': {
            'enabled': False
        },
        'cloud': {
            'enabled': True,
            'provider': 'openai',
            'model': 'gpt-3.5-turbo'
        }
    }

@pytest.fixture
def hybrid_config():
    return {
        'mode': 'hybrid',
        'decision_threshold': 0.5,
        'local': {
            'enabled': True,
            'model': 'phi3:mini',
            'base_url': 'http://localhost:11434',
            'temperature': 0.7
        },
        'cloud': {
            'enabled': True,
            'provider': 'openai',
            'model': 'gpt-3.5-turbo'
        }
    }

@pytest.mark.ai
@pytest.mark.unit
class TestLocalLLM:
    def test_initialization(self, local_config):
        llm = LocalLLM(local_config['local'])
        
        assert llm.enabled == True
        assert llm.model == 'phi3:mini'
        assert llm.base_url == 'http://localhost:11434'
        assert llm.temperature == 0.7
    
    @patch('modules.ai.local_llm.requests.get')
    def test_is_available_success(self, mock_get, local_config):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        llm = LocalLLM(local_config['local'])
        assert llm.is_available() == True
    
    @patch('modules.ai.local_llm.requests.get')
    def test_is_available_failure(self, mock_get, local_config):
        mock_get.side_effect = Exception("Connection failed")
        
        llm = LocalLLM(local_config['local'])
        assert llm.is_available() == False
    
    @patch('modules.ai.local_llm.requests.post')
    def test_generate_success(self, mock_post, local_config):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'response': 'Test response'}
        mock_post.return_value = mock_response
        
        llm = LocalLLM(local_config['local'])
        result = llm.generate("Test prompt")
        
        assert result == 'Test response'
        mock_post.assert_called_once()
    
    @patch('modules.ai.local_llm.requests.post')
    def test_generate_failure(self, mock_post, local_config):
        mock_post.side_effect = Exception("API Error")
        
        llm = LocalLLM(local_config['local'])
        result = llm.generate("Test prompt")
        
        assert result is None

@pytest.mark.ai
@pytest.mark.unit
class TestCloudLLM:
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key', 'CLOUD_AI_PROVIDER': 'openai'}, clear=True)
    def test_initialization_openai(self, cloud_config):
        llm = CloudLLM(cloud_config['cloud'])
        
        assert llm.enabled == True
        assert llm.provider == 'openai'
        assert llm.api_key == 'test-key'
    
    @patch.dict('os.environ', {}, clear=True)
    def test_initialization_no_api_key(self, cloud_config):
        llm = CloudLLM(cloud_config['cloud'])
        
        assert llm.api_key is None

@pytest.mark.ai
@pytest.mark.integration
class TestAIManager:
    def test_local_mode_initialization(self, local_config, monkeypatch):
        monkeypatch.setenv('AI_MODE', 'local')
        
        ai = AIManager(local_config)
        
        assert ai.mode == 'local'
        assert isinstance(ai.local_llm, LocalLLM)
        assert isinstance(ai.cloud_llm, CloudLLM)
    
    def test_cloud_mode_initialization(self, cloud_config, monkeypatch):
        monkeypatch.setenv('AI_MODE', 'cloud')
        
        ai = AIManager(cloud_config)
        
        assert ai.mode == 'cloud'
    
    def test_hybrid_mode_initialization(self, hybrid_config, monkeypatch):
        monkeypatch.setenv('AI_MODE', 'hybrid')
        
        ai = AIManager(hybrid_config)
        
        assert ai.mode == 'hybrid'
        assert ai.decision_threshold == 0.5
    
    @patch.object(LocalLLM, 'generate')
    def test_local_mode_generate(self, mock_generate, local_config, monkeypatch):
        monkeypatch.setenv('AI_MODE', 'local')
        mock_generate.return_value = "Local response"
        
        ai = AIManager(local_config)
        response = ai.generate("Test prompt")
        
        assert response == "Local response"
        mock_generate.assert_called_once()

    @patch.object(LocalLLM, 'generate')
    def test_personal_injection_generate(self, mock_generate, local_config, monkeypatch):
        monkeypatch.setenv('AI_MODE', 'local')
        monkeypatch.setenv('PHENOM_AGE', '35')
        local_config['personal_injection'] = {'enabled': True, 'env_keys': [], 'directive': 'Use the user info.'}
        mock_generate.return_value = "OK"

        ai = AIManager(local_config)
        response = ai.generate("Hello")

        assert response == "OK"
        mock_generate.assert_called_once()
        # The system prompt should include the PHENOM_AGE value (could be positional arg)
        called_args, called_kwargs = mock_generate.call_args
        system_arg = None
        if len(called_args) >= 2:
            system_arg = called_args[1]
        else:
            system_arg = called_kwargs.get('system')
        assert system_arg and 'PHENOM_AGE: 35' in system_arg

    @patch.object(LocalLLM, 'chat')
    def test_personal_injection_chat(self, mock_chat, local_config, monkeypatch):
        monkeypatch.setenv('AI_MODE', 'local')
        monkeypatch.setenv('PHENOM_AGE', '42')
        local_config['personal_injection'] = {'enabled': True, 'env_keys': [], 'directive': 'Use the user info.'}
        mock_chat.return_value = "Chat OK"

        ai = AIManager(local_config)
        messages = [{'role': 'user', 'content': 'Hi there'}]
        response = ai.chat(messages)

        assert response == "Chat OK"
        mock_chat.assert_called_once()
        called_args, called_kwargs = mock_chat.call_args
        sent_messages = called_args[0]
        assert sent_messages[0]['role'] == 'system'
        assert 'PHENOM_AGE: 42' in sent_messages[0]['content']
    
    @patch.object(CloudLLM, 'generate')
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    def test_cloud_mode_generate(self, mock_generate, cloud_config, monkeypatch):
        monkeypatch.setenv('AI_MODE', 'cloud')
        mock_generate.return_value = "Cloud response"
        
        ai = AIManager(cloud_config)
        response = ai.generate("Test prompt")
        
        assert response == "Cloud response"
        mock_generate.assert_called_once()
    
    @patch.object(LocalLLM, 'is_available')
    @patch.object(LocalLLM, 'generate')
    @patch.object(CloudLLM, 'is_available')
    @patch.object(CloudLLM, 'generate')
    def test_hybrid_mode_local_first(self, cloud_gen, cloud_avail, local_gen, local_avail, 
                                      hybrid_config, monkeypatch):
        monkeypatch.setenv('AI_MODE', 'hybrid')
        local_avail.return_value = True
        local_gen.return_value = "Local response"
        
        ai = AIManager(hybrid_config)
        response = ai.generate("Simple question")
        
        assert response == "Local response"
        local_gen.assert_called_once()
    
    @patch.object(LocalLLM, 'is_available')
    @patch.object(LocalLLM, 'generate')
    @patch.object(CloudLLM, 'is_available')
    @patch.object(CloudLLM, 'generate')
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    def test_hybrid_mode_fallback_to_cloud(self, cloud_gen, cloud_avail, local_gen, local_avail,
                                            hybrid_config, monkeypatch):
        monkeypatch.setenv('AI_MODE', 'hybrid')
        local_avail.return_value = False
        cloud_avail.return_value = True
        cloud_gen.return_value = "Cloud fallback response"
        
        ai = AIManager(hybrid_config)
        response = ai.generate("Complex question")
        
        assert response == "Cloud fallback response"
        cloud_gen.assert_called_once()
    
    @patch.object(LocalLLM, 'generate')
    def test_local_mode_fallback_message(self, mock_generate, local_config, monkeypatch):
        monkeypatch.setenv('AI_MODE', 'local')
        mock_generate.return_value = None
        
        ai = AIManager(local_config)
        response = ai.generate("Test")
        
        assert "trouble processing" in response.lower()

@pytest.mark.ai
@pytest.mark.unit
class TestAIManagerDecisionLogic:
    @patch.object(AIManager, '_should_use_cloud')
    @patch.object(CloudLLM, 'is_available')
    @patch.object(CloudLLM, 'generate')
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    def test_force_cloud_parameter(self, cloud_gen, cloud_avail, should_use_cloud, 
                                    hybrid_config, monkeypatch):
        monkeypatch.setenv('AI_MODE', 'hybrid')
        cloud_avail.return_value = True
        cloud_gen.return_value = "Forced cloud response"
        
        ai = AIManager(hybrid_config)
        response = ai.generate("Test", force_cloud=True)
        
        assert response == "Forced cloud response"
        cloud_gen.assert_called_once()

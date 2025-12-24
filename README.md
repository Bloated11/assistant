# phenom - Personal AI Assistant

A powerful, modular personal AI assistant inspired by phenom from Iron Man, featuring voice interaction, system automation, web search, task management, and self-learning capabilities.

## 🚀 Quick Start

### Windows (Automated Installation)
```cmd
INSTALL.bat
```
**Smart installer that:**
- ✅ Detects your GPU, RAM, CPU automatically
- ✅ Installs optimal dependencies for your hardware
- ✅ Downloads best AI models for your specs
- ✅ Configures everything automatically
- ✅ Ready in 10-15 minutes

### Linux/Mac
```bash
./START.sh
```

---

## Features

### 🎤 Voice Interaction
- Speech-to-text recognition
- Text-to-speech responses
- Wake word detection
- Natural conversation flow

### 🤖 Hybrid AI
- Local LLM support (via Ollama)
- Cloud AI integration (OpenAI, Anthropic)
- Intelligent routing between local and cloud
- Context-aware responses

### 🔧 System Automation
- Execute system commands
- Process management
- File operations
- Application launching
- System monitoring

### 🌐 Web Search
- Multi-engine search (DuckDuckGo, Wikipedia)
- Quick answers
- Content extraction
- Result summarization

### ✅ Task Management
- Create and manage tasks
- Priority levels
- Due dates and reminders
- Task filtering and search

### 🧠 Learning & Memory
- Conversation history
- Pattern recognition
- User preferences
- Fact storage and recall
- Contextual responses

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager
- (Optional) Ollama for local AI
- (Optional) API keys for cloud AI services

### Quick Start

1. **Clone or navigate to the directory:**
   ```bash
   cd /home/aj/phenom
   ```

2. **Run the setup script:**
   ```bash
   python setup.py
   ```

3. **Install system dependencies (Linux):**
   ```bash
   sudo apt-get install portaudio19-dev python3-pyaudio
   ```

4. **Install Ollama (for local AI):**
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ollama pull llama3.2
   ```

5. **Configure (optional):**
   - Copy `.env.example` to `.env`
   - Add your API keys if using cloud AI
   - Customize `config/config.yaml`

## Usage

### Text Mode
```bash
python main.py --mode text
```
Interactive text-based conversation.

### Voice Mode
```bash
python main.py --mode voice
```
Voice-activated interaction with wake word detection.

### Hybrid Mode (Default)
```bash
python main.py
```
Choose between voice and text mode at runtime.

## Commands

### System Control
- "system status" - Get system information
- "execute [command]" - Run a system command
- "open [app]" - Launch an application
- "list processes" - Show running processes
- "kill process [PID]" - Terminate a process

### Web & Search
- "search for [query]" - Search the web
- "what is [query]" - Get quick answers
- "find information about [topic]" - Research topics

### Task Management
- "add task [title]" - Create a new task
- "list tasks" - Show pending tasks
- "complete task [id]" - Mark task as complete
- "task summary" - Get task statistics

### Memory
- "remember [fact]" - Store information
- "recall [key]" - Retrieve stored information
- "what did we discuss" - Review conversation history

### General
- "status" - Check phenom status
- "help" - Show available commands

## Configuration

Edit `config/config.yaml` to customize:

- Voice settings (rate, volume, engine)
- AI mode (local, cloud, hybrid)
- Module toggles
- Security settings
- Logging preferences

## Project Structure

```
phenom/
├── config/
│   └── config.yaml          # Main configuration
├── modules/
│   ├── voice/               # Voice interaction
│   ├── automation/          # System control
│   ├── web_search/          # Web search capabilities
│   ├── tasks/               # Task management
│   ├── ai/                  # AI integration
│   └── learning/            # Memory & learning
├── data/                    # Data storage
├── logs/                    # Log files
├── core.py                  # Main phenom class
├── command_processor.py     # Command interpretation
├── main.py                  # Entry point
└── setup.py                 # Setup script
```

## Security Notes

- System commands require confirmation by default
- Dangerous operations require explicit approval
- All commands are logged
- API keys should be stored in `.env` file (never commit)

## Troubleshooting

### Voice not working
- Ensure PyAudio is installed
- Check microphone permissions
- Test microphone with `arecord` (Linux) or system settings

### Local AI not responding
- Verify Ollama is running: `ollama serve`
- Check model is pulled: `ollama list`
- Test with: `ollama run llama3.2`

### Cloud AI not working
- Verify API key is set correctly
- Check internet connection
- Review logs in `logs/phenom.log`

## Contributing

This is a personal project, but feel free to fork and customize for your needs.

## License

MIT License - Feel free to use and modify.

## Acknowledgments

Inspired by phenom from the Iron Man/MCU franchise.
Built with Python and various open-source libraries.
# assistant
# assistant

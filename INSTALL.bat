@echo off
setlocal EnableDelayedExpansion

REM ============================================
REM PHENOM AI — ELITE WINDOWS INSTALLER + LAUNCHER
REM ============================================

color 0A
title Phenom AI - Smart Installer

echo.
echo ============================================
echo    PHENOM AI - Smart Installer (Windows)
echo ============================================
echo.
echo This installer will:
echo  - Detect your PC configuration
echo  - Recommend optimal AI settings
echo  - Ask for your preferences
echo  - Install dependencies
echo  - Download the right AI models
echo  - Configure, verify, and launch Phenom
echo.
pause

REM ============================================
REM STEP 1: SYSTEM DETECTION
REM ============================================

echo.
echo ============================================
echo  STEP 1: Detecting System Configuration
echo ============================================
echo.

set GPU_TYPE=None
set GPU_NAME=Unknown
set VRAM_MB=0

nvidia-smi >nul 2>&1
if %errorlevel%==0 (
    set GPU_TYPE=NVIDIA
    for /f "delims=" %%a in ('nvidia-smi --query-gpu=name --format=csv,noheader') do set GPU_NAME=%%a
    for /f "delims=" %%a in ('nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits') do set VRAM_MB=%%a
)

for /f "tokens=2 delims==" %%a in ('wmic ComputerSystem get TotalPhysicalMemory /value') do set RAM_BYTES=%%a
set /a RAM_GB=!RAM_BYTES:~0,-9!

for /f "tokens=2 delims==" %%a in ('wmic cpu get NumberOfLogicalProcessors /value') do set CPU_CORES=%%a

python --version >nul 2>&1 || (
    echo ❌ Python not found. Install Python 3.11+ and add to PATH.
    pause
    exit /b 1
)

for /f "tokens=2" %%a in ('python --version') do set PYTHON_VERSION=%%a

echo GPU       : !GPU_TYPE! - !GPU_NAME!
echo VRAM      : !VRAM_MB! MB
echo RAM       : !RAM_GB! GB
echo CPU Cores : !CPU_CORES!
echo Python    : !PYTHON_VERSION!
echo.

REM ============================================
REM STEP 2: AI RECOMMENDATION ENGINE
REM ============================================

set AI_MODE=cloud
set MODEL=none
set CONTEXT=2048
set VECTOR_DB=faiss
set TIER=CPU / Cloud

if !VRAM_MB! GEQ 24000 (
    set AI_MODE=local
    set MODEL=llama3.1:70b
    set CONTEXT=8192
    set VECTOR_DB=chromadb
    set TIER=High-End GPU
) else if !VRAM_MB! GEQ 12000 (
    set AI_MODE=hybrid
    set MODEL=llama3.1:8b
    set CONTEXT=4096
    set VECTOR_DB=chromadb
    set TIER=Mid-Range GPU
) else if !VRAM_MB! GEQ 6000 (
    set AI_MODE=hybrid
    set MODEL=phi3:medium
    set CONTEXT=2048
    set VECTOR_DB=faiss
    set TIER=Entry-Level GPU
)

echo ============================================
echo  AI Recommendation
echo ============================================
echo System Tier       : !TIER!
echo Recommended Mode : !AI_MODE!
echo Recommended Model: !MODEL!
echo Context Window   : !CONTEXT!
echo.

REM ============================================
REM STEP 3: USER PREFERENCES
REM ============================================

echo Select AI Mode:
echo   1) Local
echo   2) Cloud
echo   3) Hybrid
echo   4) Recommended (!AI_MODE!)
set /p MODE_CHOICE=Choice [4]:
if "!MODE_CHOICE!"=="" set MODE_CHOICE=4

if "!MODE_CHOICE!"=="1" set AI_MODE=local
if "!MODE_CHOICE!"=="2" set AI_MODE=cloud
if "!MODE_CHOICE!"=="3" set AI_MODE=hybrid

echo ✓ Selected Mode: !AI_MODE!
echo.

REM --------------------------------------------
REM Local Model Selection (SMART + SAFE)
REM --------------------------------------------

if not "!AI_MODE!"=="cloud" (
    if "!MODEL!"=="none" (
        echo No heavy local model recommended.
        echo Using guaranteed fallback: phi3:mini
        set MODEL=phi3:mini
    ) else (
        echo Recommended local model: !MODEL!
        set /p USE_MODEL=Use this model? [Y/n]:
        if /i "!USE_MODEL!"=="n" (
            set /p USER_MODEL=Enter Ollama model (blank = phi3:mini):
            if "!USER_MODEL!"=="" (
                set MODEL=phi3:mini
            ) else (
                set MODEL=!USER_MODEL!
            )
        )
    )
)

REM --------------------------------------------
REM Cloud Provider
REM --------------------------------------------

if not "!AI_MODE!"=="local" (
    echo.
    echo Select Cloud Provider:
    echo   1) OpenAI
    echo   2) Anthropic
    echo   3) OpenRouter
    set /p CLOUD_CHOICE=Choice [1]:
    if "!CLOUD_CHOICE!"=="2" set CLOUD_PROVIDER=anthropic
    if "!CLOUD_CHOICE!"=="3" set CLOUD_PROVIDER=openrouter
    if "!CLOUD_CHOICE!"=="" set CLOUD_PROVIDER=openai
) else (
    set CLOUD_PROVIDER=none
)

REM ============================================
REM STEP 4: PYTHON ENVIRONMENT
REM ============================================

if not exist .venv (
    python -m venv .venv
)

call .venv\Scripts\activate
python -m pip install --upgrade pip

if "!GPU_TYPE!"=="NVIDIA" (
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
) else (
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
)

pip install -r requirements.txt
pip install pyttsx3 SpeechRecognition PyAudio 2>nul

REM ============================================
REM STEP 5: OLLAMA MODELS
REM ============================================

if not "!AI_MODE!"=="cloud" (
    where ollama >nul 2>&1 || (
        echo ❌ Ollama not installed.
        echo Download from: https://ollama.com
        pause
        exit /b 1
    )

    echo Installing local model: !MODEL!
    ollama pull !MODEL! || echo ⚠️ Model pull failed
)

REM ============================================
REM STEP 6: CONFIGURATION
REM ============================================

if not exist config mkdir config

set /a THREADS=!CPU_CORES!/2
if !THREADS! LSS 2 set THREADS=2
if !THREADS! GTR 8 set THREADS=8

(
echo ai:
echo   mode: "!AI_MODE!"
echo   local:
echo     enabled: !AI_MODE! NEQ cloud
echo     model: "!MODEL!"
echo     base_url: "http://localhost:11434"
echo     num_ctx: !CONTEXT!
echo     num_thread: !THREADS!
echo   cloud:
echo     provider: "!CLOUD_PROVIDER!"
echo.
echo vector_db:
echo   provider: "!VECTOR_DB!"
) > config\config.yaml

if not exist .env (
(
echo AI_MODE=!AI_MODE!
echo LOCAL_AI_MODEL=!MODEL!
echo CLOUD_AI_PROVIDER=!CLOUD_PROVIDER!
echo.
echo OPENAI_API_KEY=
echo ANTHROPIC_API_KEY=
echo OPENROUTER_API_KEY=
# ===================================
# Phenom AI Assistant - Environment Configuration

# General Settings
PHENOM_NAME=phenom
PHENOM_WAKE_WORD=phenom

# Bing Web Search API (for web search - free tier available)
# Get your key from: https://www.microsoft.com/en-us/bing/apis/bing-web-search-api
# Free tier: 1000 queries/month
BING_SEARCH_API_KEY=

# OpenWeatherMap API (optional - free tier available)
# Get your key from: https://openweathermap.org/api
# Leave empty to use free wttr.in service
WEATHER_API_KEY=

# Weather Location (city name or coordinates)
WEATHER_LOCATION=auto
WEATHER_UNITS=metric

# ----------------
# Calendar Integration
# ----------------

# Google Calendar API Credentials
# Get credentials from: https://console.cloud.google.com/
GOOGLE_CALENDAR_CREDENTIALS_FILE=config/google_credentials.json
GOOGLE_CALENDAR_TOKEN_FILE=config/google_token.json



# ----------------
# Database
# ----------------

# SQLite Database Path
DATABASE_PATH=data/phenom.db

# ----------------
# Storage Paths
# ----------------

# Task Storage
TASKS_STORAGE=data/tasks.json

# Memory & Learning
MEMORY_FILE=data/memory.json
CONVERSATION_HISTORY=data/conversations.json

# ----------------
# Security & Encryption
# ----------------

# Master Password for Security Vault (optional)
SECURITY_VAULT_PASSWORD=

# API Authentication Token (for REST API access)
API_AUTH_TOKEN=

# ----------------
# Optional Integrations
# ----------------

# News API (optional - for advanced news features)
# Get key from: https://newsapi.org/
NEWS_API_KEY=

# Spotify API (for media control)
SPOTIFY_CLIENT_ID=
SPOTIFY_CLIENT_SECRET=

# GitHub API (for code assistant features)
GITHUB_TOKEN=

# ----------------
# Performance Settings
# ----------------

# Ollama Server URL (for local AI)
OLLAMA_BASE_URL=http://localhost:11434


# Thread Count (use all CPU cores for speed)
AI_NUM_THREADS=4

# ----------------
# Logging & Debug
# ----------------

# Log Level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO

# Log File Path
LOG_FILE=logs/phenom.log

# ----------------
# Voice Settings
# ----------------

# Voice Recognition Language
VOICE_LANGUAGE=en-US

# Speech Rate (words per minute)
SPEECH_RATE=150

# Voice Volume (0.0 to 1.0)
VOICE_VOLUME=0.8

) > .env
)

REM ============================================
REM STEP 7: VERIFICATION
REM ============================================

echo.
echo Verifying installation...
python -c "import torch; from core import Phenom; p = Phenom(); print(f'✓ {p.name.upper()} ready')"

REM ============================================
REM STEP 8: LAUNCH PHENOM 
REM ============================================

echo.
echo ============================================
echo   PHENOM AI ASSISTANT
echo ============================================
echo.

echo Checking GPU...
python -c "import torch; print(f'GPU Available: {torch.cuda.is_available()}'); print(f'GPU Name: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"CPU Only\"}')" 2>nul
echo.

echo Initializing Phenom...
python -c "from core import Phenom; p = Phenom(); print(f'✓ {p.name.upper()} ready with {len([k for k,v in p.get_status()[\"modules\"].items() if v])}/35 modules loaded')" 2>nul

if %errorlevel% neq 0 (
    echo ✗ Failed to initialize Phenom
    pause
    exit /b 1
)

echo.
echo ============================================
echo   SELECT MODE
echo ============================================
echo 1) Web Mode (GUI)
echo 2) Voice Mode
echo 3) Text Mode
echo 4) Exit
echo.

set /p choice=Enter your choice (1-4):

if "%choice%"=="1" (
    python run_web.py
) else if "%choice%"=="2" (
    python main.py --mode voice
) else if "%choice%"=="3" (
    python main.py --mode text
) else (
    echo Exiting...
)

endlocal

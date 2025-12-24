#!/usr/bin/env bash
set -Eeuo pipefail
trap 'echo "❌ Error on line $LINENO"; exit 1' ERR

# ==================================================
# PHENOM AI — SMART INSTALLER + LAUNCHER (INTERACTIVE)
# ==================================================

VENV=".venv"
CONFIG_DIR="config"
CONFIG_FILE="$CONFIG_DIR/config.yaml"
ENV_FILE=".env"

exists() { command -v "$1" >/dev/null 2>&1; }
pause() { read -rp "Press ENTER to continue..."; }
section() {
  echo
  echo "============================================"
  echo " $1"
  echo "============================================"
}

clear 2>/dev/null || true
section "PHENOM AI — SMART INSTALLER"

echo "This installer will:"
echo " • Detect your system"
echo " • Recommend AI configuration"
echo " • Ask for your preferences"
echo " • Install dependencies"
echo " • Configure & launch Phenom"
pause

# --------------------------------------------------
# Preflight
# --------------------------------------------------

section "PRE-FLIGHT CHECKS"

for cmd in python3 awk sed curl; do
  exists "$cmd" || { echo "❌ Missing required command: $cmd"; exit 1; }
done

if ! exists apt; then
  echo "❌ Debian/Ubuntu-based systems only"
  exit 1
fi

PY_VER=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✓ Python $PY_VER detected"

# --------------------------------------------------
# System Detection
# --------------------------------------------------

section "SYSTEM DETECTION"

GPU_TYPE="none"
GPU_NAME="N/A"
VRAM_MB=0

if exists nvidia-smi; then
  GPU_TYPE="nvidia"
  GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -n1)
  VRAM_MB=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -n1)
fi

RAM_GB=$(free -g | awk '/^Mem:/ {print $2}')
CPU_CORES=$(nproc)

echo "CPU Cores : $CPU_CORES"
echo "RAM       : ${RAM_GB} GB"
echo "GPU       : $GPU_TYPE ($GPU_NAME)"
echo "VRAM      : ${VRAM_MB} MB"

# --------------------------------------------------
# Recommendation Engine
# --------------------------------------------------

section "AI RECOMMENDATIONS"

AI_MODE="cloud"
MODEL="none"
CONTEXT=2048
VECTOR_DB="faiss"

if [[ "$GPU_TYPE" == "nvidia" && $VRAM_MB -ge 24000 ]]; then
  AI_MODE="local"
  MODEL="llama3.1:70b"
  CONTEXT=8192
  VECTOR_DB="chromadb"
  TIER="High-End GPU"
elif [[ "$GPU_TYPE" == "nvidia" && $VRAM_MB -ge 12000 ]]; then
  AI_MODE="hybrid"
  MODEL="llama3.1:8b"
  CONTEXT=4096
  VECTOR_DB="chromadb"
  TIER="Mid-Range GPU"
elif [[ "$GPU_TYPE" == "nvidia" && $VRAM_MB -ge 6000 ]]; then
  AI_MODE="hybrid"
  MODEL="phi3:medium"
  TIER="Entry-Level GPU"
else
  TIER="CPU / Cloud"
fi

echo "System Tier       : $TIER"
echo "Recommended Mode  : $AI_MODE"
echo "Recommended Model : $MODEL"
echo "Context Window    : $CONTEXT"

# --------------------------------------------------
# User Choices
# --------------------------------------------------

section "USER PREFERENCES"

echo "Select AI Mode:"
echo "  1) Local"
echo "  2) Cloud"
echo "  3) Hybrid"
echo "  4) Recommended ($AI_MODE)"
read -rp "Choice [4]: " MODE_CHOICE
MODE_CHOICE=${MODE_CHOICE:-4}

case "$MODE_CHOICE" in
  1) AI_MODE="local" ;;
  2) AI_MODE="cloud" ;;
  3) AI_MODE="hybrid" ;;
esac

echo "✓ Selected mode: $AI_MODE"

# --------------------------------------------------
# Local Model Selection (SMART + SAFE)
# --------------------------------------------------

if [[ "$AI_MODE" != "cloud" ]]; then
  if [[ "$MODEL" == "none" ]]; then
    echo
    echo "No heavy local model recommended for this system."
    echo "Using lightweight fallback model: phi3:mini"
    MODEL="phi3:mini"
  else
    echo
    echo "Recommended local model: $MODEL"
    read -rp "Use this model? [Y/n]: " USE_MODEL
    USE_MODEL=${USE_MODEL:-Y}

    if [[ ! "$USE_MODEL" =~ ^[Yy]$ ]]; then
      read -rp "Enter Ollama model name (or leave blank for phi3:mini): " USER_MODEL
      USER_MODEL="${USER_MODEL//[[:space:]]/}"
      MODEL="${USER_MODEL:-phi3:mini}"
    fi
  fi
fi

# --------------------------------------------------
# Cloud Provider
# --------------------------------------------------

if [[ "$AI_MODE" != "local" ]]; then
  echo
  echo "Select Cloud Provider:"
  echo "  1) OpenAI"
  echo "  2) Anthropic"
  echo "  3) OpenRouter"
  read -rp "Choice [1]: " CLOUD_CHOICE
  CLOUD_CHOICE=${CLOUD_CHOICE:-1}

  case "$CLOUD_CHOICE" in
    2) CLOUD_PROVIDER="anthropic" ;;
    3) CLOUD_PROVIDER="openrouter" ;;
    *) CLOUD_PROVIDER="openai" ;;
  esac
else
  CLOUD_PROVIDER="none"
fi

# --------------------------------------------------
# Install Dependencies
# --------------------------------------------------

section "INSTALLING DEPENDENCIES"

sudo apt update
sudo apt install -y \
  python3-venv python3-pip \
  build-essential git curl wget \
  espeak espeak-data libespeak-dev \
  portaudio19-dev alsa-utils libasound2-dev

# --------------------------------------------------
# Python Environment
# --------------------------------------------------

section "PYTHON ENVIRONMENT"

[[ -d "$VENV" ]] || python3 -m venv "$VENV"
source "$VENV/bin/activate"
pip install --upgrade pip

if [[ "$GPU_TYPE" == "nvidia" ]]; then
  pip install torch torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/cu121
else
  pip install torch torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/cpu
fi

pip install -r requirements.txt
pip install pyttsx3 SpeechRecognition PyAudio

# --------------------------------------------------
# Ollama (Deterministic Model Installation)
# --------------------------------------------------

section "OLLAMA"

if [[ "$AI_MODE" == "cloud" ]]; then
  echo "Cloud-only mode selected — skipping Ollama setup"
else
  if ! exists ollama; then
    echo "⚠️ Ollama is not installed"
    echo "Install it with:"
    echo "  curl -fsSL https://ollama.com/install.sh | sh"
  else
    echo "✓ Ollama detected"

    echo
    echo "Installing required local model: $MODEL"
    if ollama pull "$MODEL"; then
      echo "✓ $MODEL ready"
    else
      echo "⚠️ Failed to pull $MODEL"
      echo "Local AI may be unavailable"
    fi
  fi
fi

# --------------------------------------------------
# Config Files
# --------------------------------------------------

section "GENERATING CONFIGURATION"

mkdir -p "$CONFIG_DIR"
[[ -f "$CONFIG_FILE" ]] && cp "$CONFIG_FILE" "$CONFIG_FILE.bak"

THREADS=$((CPU_CORES / 2))
THREADS=$(( THREADS < 2 ? 2 : THREADS > 8 ? 8 : THREADS ))

cat > "$CONFIG_FILE" <<EOF
ai:
  mode: "$AI_MODE"
  local:
    enabled: $( [[ "$AI_MODE" == "cloud" ]] && echo false || echo true )
    model: "$MODEL"
    base_url: "http://localhost:11434"
    num_ctx: $CONTEXT
    num_thread: $THREADS
    num_gpu: $( [[ "$GPU_TYPE" == "nvidia" ]] && echo 1 || echo 0 )
  cloud:
    enabled: $( [[ "$AI_MODE" == "local" ]] && echo false || echo true )
    provider: "$CLOUD_PROVIDER"

vector_db:
  provider: "$VECTOR_DB"
EOF

if [[ ! -f "$ENV_FILE" ]]; then
cat > "$ENV_FILE" <<EOF
AI_MODE=$AI_MODE
LOCAL_AI_MODEL=$MODEL
CLOUD_AI_PROVIDER=$CLOUD_PROVIDER

OPENAI_API_KEY=
ANTHROPIC_API_KEY=
OPENROUTER_API_KEY=
# ===================================
# Phenom AI Assistant - Environment Configuration

# General Settings
PHENOM_NAME=phenom
PHENOM_WAKE_WORD=phenom

# AI Configuration
# AI Mode: local (Ollama), cloud (OpenAI/Anthropic/OpenRouter), or hybrid
# hybrid = local first, fallback to cloud if needed
AI_MODE=hybrid
# CLOUD_AI_PROVIDER options: openai, anthropic, openrouter
CLOUD_AI_PROVIDER=openai

# API Keys
# OpenAI API: https://platform.openai.com/api-keys
# Anthropic API: https://console.anthropic.com/
# OpenRouter API: https://openrouter.ai/keys
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
OPENROUTER_API_KEY=

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

EOF
else
  sed -i "s/^AI_MODE=.*/AI_MODE=$AI_MODE/" "$ENV_FILE"
  sed -i "s/^LOCAL_AI_MODEL=.*/LOCAL_AI_MODEL=$MODEL/" "$ENV_FILE"
  sed -i "s/^CLOUD_AI_PROVIDER=.*/CLOUD_AI_PROVIDER=$CLOUD_PROVIDER/" "$ENV_FILE"
fi

# --------------------------------------------------
# Verification
# --------------------------------------------------

section "VERIFYING INSTALLATION"

python3 - <<EOF
import torch
from core import Phenom
print("Torch CUDA:", torch.cuda.is_available())
p = Phenom()
print(f"✓ {p.name.upper()} initialized")
EOF

# --------------------------------------------------
# Launcher
# --------------------------------------------------

section "PHENOM READY"

echo "Select Interaction Mode:"
echo "  1) Web"
echo "  2) Voice"
echo "  3) Text"
echo "  4) Exit"

read -rp "Choice: " MODE

case "${MODE,,}" in
  1|web) python3 run_web.py ;;
  2|voice) python3 main.py --mode voice ;;
  3|text) python3 main.py --mode text ;;
  4|exit|quit) exit 0 ;;
  *) echo "Invalid choice. Exiting..."; exit 1 ;;
esac

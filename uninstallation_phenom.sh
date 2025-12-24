#!/usr/bin/env bash
set -e

# ============================================
# Phenom AI - Uninstaller (Linux)
# ============================================

clear
echo "============================================"
echo "   PHENOM AI - UNINSTALLER (LINUX)"
echo "============================================"
echo
echo "This will remove Phenom AI from this folder."
echo "It will NOT remove system Python or other projects."
echo
read -rp "Continue? (y/n): " CONFIRM
[[ "$CONFIRM" != "y" ]] && exit 0

# ============================================
# STEP 1: Stop running processes
# ============================================

echo
echo "============================================"
echo " STEP 1: Stopping Phenom Processes"
echo "============================================"

pkill -f "python.*Phenom" 2>/dev/null || true
pkill -f "ollama" 2>/dev/null || true

echo "[✓] Any running Phenom processes stopped"

# ============================================
# STEP 2: Remove virtual environment
# ============================================

echo
echo "============================================"
echo " STEP 2: Removing Virtual Environment"
echo "============================================"

if [[ -d ".venv" ]]; then
    rm -rf .venv
    echo "[✓] Virtual environment removed"
else
    echo "[i] No virtual environment found"
fi

# ============================================
# STEP 3: Remove generated configuration
# ============================================

echo
echo "============================================"
echo " STEP 3: Removing Configuration Files"
echo "============================================"

FILES_TO_REMOVE=(
    "config/config.yaml"
    ".env"
)

for FILE in "${FILES_TO_REMOVE[@]}"; do
    if [[ -f "$FILE" ]]; then
        rm -f "$FILE"
        echo "[✓] Removed $FILE"
    else
        echo "[i] $FILE not found"
    fi
done

# Remove vector database
if [[ -d "data/vector_db" ]]; then
    rm -rf data/vector_db
    echo "[✓] Vector database removed"
fi

# ============================================
# STEP 4: Remove downloaded AI models (Optional)
# ============================================

echo
echo "============================================"
echo " STEP 4: Local AI Models (Optional)"
echo "============================================"
echo
echo "Do you want to remove downloaded Ollama models?"
echo "This may free many GB of disk space."
read -rp "Remove Ollama models? (y/n): " REMOVE_MODELS

if [[ "$REMOVE_MODELS" == "y" ]]; then
    if command -v ollama >/dev/null 2>&1; then
        ollama rm llama3.1:70b 2>/dev/null || true
        ollama rm llama3.1:8b 2>/dev/null || true
        ollama rm phi3:medium 2>/dev/null || true
        ollama rm phi3:mini 2>/dev/null || true
        echo "[✓] Ollama models removed"
    else
        echo "[i] Ollama not installed"
    fi
else
    echo "[i] Ollama models preserved"
fi

# ============================================
# STEP 5: Remove Ollama itself (Optional)
# ============================================

echo
echo "============================================"
echo " STEP 5: Ollama Application (Optional)"
echo "============================================"
echo
read -rp "Uninstall Ollama entirely? (y/n): " REMOVE_OLLAMA

if [[ "$REMOVE_OLLAMA" == "y" ]]; then
    if command -v ollama >/dev/null 2>&1; then
        sudo systemctl stop ollama 2>/dev/null || true
        sudo systemctl disable ollama 2>/dev/null || true
        sudo rm -f /usr/local/bin/ollama
        sudo rm -rf /usr/local/lib/ollama
        sudo rm -rf /usr/share/ollama
        sudo rm -rf ~/.ollama
        echo "[✓] Ollama removed"
    else
        echo "[i] Ollama not found"
    fi
else
    echo "[i] Ollama kept"
fi

# ============================================
# STEP 6: Clean cache/logs
# ============================================

echo
echo "============================================"
echo " STEP 6: Cleaning Caches & Logs"
echo "============================================"

rm -rf __pycache__ 2>/dev/null || true
rm -rf logs 2>/dev/null || true
rm -rf data/cache 2>/dev/null || true

echo "[✓] Cache cleaned"

# ============================================
# COMPLETE
# ============================================

echo
echo "============================================"
echo " UNINSTALL COMPLETE"
echo "============================================"
echo
echo "What was removed:"
echo "  - Virtual environment (.venv)"
echo "  - Phenom configuration files"
echo "  - Vector database"
echo
echo "What was NOT removed:"
echo "  - System Python"
echo "  - Other Python projects"
echo
echo "You can reinstall anytime by running:"
echo "  ./install_phenom.sh"
echo

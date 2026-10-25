#!/usr/bin/env bash
# ==============================================================================
# Script: serve.sh
# Purpose: Build Ollama model from GGUF and start OpenAI-compatible API server
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

MODEL_NAME="rag-llama3-grounded"
OLLAMA_PORT="${OLLAMA_PORT:-11434}"
OLLAMA_HOST="${OLLAMA_HOST:-127.0.0.1}"

echo "============================================================"
echo " Starting Ollama Grounded RAG Serving Pipeline"
echo " Model Tag: ${MODEL_NAME}"
echo " Endpoint:  http://${OLLAMA_HOST}:${OLLAMA_PORT}/v1"
echo "============================================================"

# 1. Check if Ollama is installed
if ! command -v ollama &>/dev/null; then
    echo "[X] Error: Ollama binary not found in PATH."
    echo "    Please install Ollama:"
    echo "    - macOS: brew install ollama  OR  download from https://ollama.com/download"
    echo "    - Linux: curl -fsSL https://ollama.com/install.sh | sh"
    exit 1
fi

echo "[✓] Ollama binary detected: $(which ollama)"

# 2. Locate the exported GGUF file
TARGET_GGUF="${SCRIPT_DIR}/llama-3-8b-Instruct.Q4_K_M.gguf"

if [[ ! -f "${TARGET_GGUF}" ]]; then
    if [[ -f "${SCRIPT_DIR}/model-unsloth.Q4_K_M.gguf" && ! "$(file -b "${SCRIPT_DIR}/model-unsloth.Q4_K_M.gguf")" =~ "JSON" ]]; then
        echo "[+] Found model-unsloth.Q4_K_M.gguf. Linking to ${TARGET_GGUF} ..."
        ln -sf "${SCRIPT_DIR}/model-unsloth.Q4_K_M.gguf" "${TARGET_GGUF}"
    elif [[ -f "${SCRIPT_DIR}/rag_grounded_llama3_gguf/llama-3-8b-Instruct.Q4_K_M.gguf" ]]; then
        echo "[+] Found GGUF in rag_grounded_llama3_gguf. Linking to ${TARGET_GGUF} ..."
        ln -sf "${SCRIPT_DIR}/rag_grounded_llama3_gguf/llama-3-8b-Instruct.Q4_K_M.gguf" "${TARGET_GGUF}"
    elif compgen -G "${SCRIPT_DIR}/*.Q4_K_M.gguf" > /dev/null; then
        FOUND_GGUF=$(ls ${SCRIPT_DIR}/*.Q4_K_M.gguf | head -n 1)
        if [[ ! "$(file -b "${FOUND_GGUF}")" =~ "JSON" ]]; then
            echo "[+] Detected GGUF file: ${FOUND_GGUF}. Linking to ${TARGET_GGUF} ..."
            ln -sf "${FOUND_GGUF}" "${TARGET_GGUF}"
        fi
    fi
fi

# 3. Validate GGUF file integrity
if [[ -f "${TARGET_GGUF}" ]]; then
    FILE_TYPE=$(file -b "${TARGET_GGUF}")
    if [[ "${FILE_TYPE}" =~ "JSON" ]]; then
        echo "------------------------------------------------------------"
        echo "[!] WARNING: ${TARGET_GGUF} is a JSON notebook file, not binary weights."
        echo "    Download 'llama-3-8b-Instruct.Q4_K_M.gguf' (~4.9 GB) from Colab's 'rag_grounded_llama3_gguf' folder."
        echo "------------------------------------------------------------"
        exit 1
    fi
    echo "[✓] Valid binary GGUF detected: ${TARGET_GGUF} ($(du -h "${TARGET_GGUF}" | cut -f1))"
else
    echo "[!] Warning: '${TARGET_GGUF}' not found."
    echo "    Please download 'llama-3-8b-Instruct.Q4_K_M.gguf' from Google Colab into: ${SCRIPT_DIR}"
    exit 1
fi

# 4. Ensure Ollama daemon is running
echo "[+] Checking if Ollama daemon is active on port ${OLLAMA_PORT}..."
if ! curl -s "http://${OLLAMA_HOST}:${OLLAMA_PORT}/api/tags" &>/dev/null; then
    echo "[+] Ollama server is not running. Starting background server..."
    export OLLAMA_HOST="${OLLAMA_HOST}:${OLLAMA_PORT}"
    ollama serve > "${SCRIPT_DIR}/ollama_server.log" 2>&1 &
    SERVER_PID=$!
    echo "[+] Ollama server process started (PID: ${SERVER_PID}). Waiting for health check..."

    MAX_RETRIES=15
    RETRY_COUNT=0
    until curl -s "http://${OLLAMA_HOST}:${OLLAMA_PORT}/api/tags" &>/dev/null; do
        sleep 1
        RETRY_COUNT=$((RETRY_COUNT + 1))
        if [[ ${RETRY_COUNT} -ge ${MAX_RETRIES} ]]; then
            echo "[X] Error: Timed out waiting for Ollama server to become ready."
            cat "${SCRIPT_DIR}/ollama_server.log"
            exit 1
        fi
    done
fi

echo "[✓] Ollama server is responding at http://${OLLAMA_HOST}:${OLLAMA_PORT}"

# 5. Register/Build model from Modelfile
echo "[+] Building Ollama model '${MODEL_NAME}' from Modelfile..."
ollama create "${MODEL_NAME}" -f "${SCRIPT_DIR}/Modelfile"
echo "[✓] Model '${MODEL_NAME}' built successfully!"

# 6. List available models
echo -e "\n[+] Current registered Ollama models:"
ollama list

# 7. Verify OpenAI-compatible endpoint
echo -e "\n[+] Verifying OpenAI-compatible /v1/models endpoint..."
curl -s "http://${OLLAMA_HOST}:${OLLAMA_PORT}/v1/models" | jq . || curl -s "http://${OLLAMA_HOST}:${OLLAMA_PORT}/v1/models"

echo -e "\n============================================================"
echo " [✓] Local RAG Inference Server is LIVE!"
echo " OpenAI API Base: http://${OLLAMA_HOST}:${OLLAMA_PORT}/v1"
echo " Chat Endpoint:   http://${OLLAMA_HOST}:${OLLAMA_PORT}/v1/chat/completions"
echo " Model Name:      ${MODEL_NAME}"
echo ""
echo " To run verification tests:"
echo "   python3 test_inference.py"
echo "============================================================"

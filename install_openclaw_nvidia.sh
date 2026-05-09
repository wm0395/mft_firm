#!/usr/bin/env bash

set -euo pipefail

echo "========================================"
echo "OpenClaw + NVIDIA Nemotron Installer"
echo "========================================"

# -----------------------------
# CONFIG
# -----------------------------

export NVIDIA_API_KEY="${NVIDIA_API_KEY:-}"

MODEL="nvidia/nemotron-3-super"
BASE_URL="https://integrate.api.nvidia.com/v1"

OPENCLAW_DIR="$HOME/.openclaw"
CONFIG_DIR="$OPENCLAW_DIR/config"
CONFIG_FILE="$CONFIG_DIR/providers.json"

# -----------------------------
# CHECK API KEY
# -----------------------------

if [ -z "$NVIDIA_API_KEY" ]; then
    echo ""
    echo "ERROR: NVIDIA_API_KEY is not set."
    echo ""
    echo "Run:"
    echo 'export NVIDIA_API_KEY="your_key_here"'
    echo ""
    exit 1
fi

# -----------------------------
# INSTALL SYSTEM DEPS
# -----------------------------

echo ""
echo "[1/7] Installing dependencies..."

if command -v apt >/dev/null 2>&1; then
    sudo apt update

    sudo apt install -y \
        curl \
        git \
        build-essential \
        bubblewrap
fi

# -----------------------------
# INSTALL NODE
# -----------------------------

echo ""
echo "[2/7] Checking Node.js..."

if ! command -v node >/dev/null 2>&1; then
    echo "Installing Node.js..."

    curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
    sudo apt install -y nodejs
fi

echo "Node version:"
node --version

# -----------------------------
# INSTALL PNPM
# -----------------------------

echo ""
echo "[3/7] Checking pnpm..."

if ! command -v pnpm >/dev/null 2>&1; then
    npm install -g pnpm
fi

echo "pnpm version:"
pnpm --version

# -----------------------------
# INSTALL OPENCLAW
# -----------------------------

echo ""
echo "[4/7] Installing OpenClaw..."

if ! command -v openclaw >/dev/null 2>&1; then
    curl -fsSL https://openclaw.ai/install.sh | bash
fi

echo "OpenClaw version:"
openclaw --version || true

# -----------------------------
# CREATE CONFIG
# -----------------------------

echo ""
echo "[5/7] Configuring NVIDIA provider..."

mkdir -p "$CONFIG_DIR"

cat > "$CONFIG_FILE" <<EOF
{
  "default_provider": "nvidia",
  "providers": {
    "nvidia": {
      "type": "openai-compatible",
      "base_url": "${BASE_URL}",
      "api_key_env": "NVIDIA_API_KEY",
      "models": [
        {
          "id": "${MODEL}",
          "supports_tools": true,
          "supports_reasoning": true,
          "context_window": 1000000
        }
      ]
    }
  }
}
EOF

echo ""
echo "Provider config:"
cat "$CONFIG_FILE"

# -----------------------------
# VERIFY API
# -----------------------------

echo ""
echo "[6/7] Testing NVIDIA API connectivity..."

HTTP_CODE=$(curl -s -o /tmp/nvidia_test.json -w "%{http_code}" \
  -X POST "${BASE_URL}/chat/completions" \
  -H "Authorization: Bearer ${NVIDIA_API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"${MODEL}\",
    \"messages\": [
      {
        \"role\": \"user\",
        \"content\": \"Reply with exactly: NVIDIA_OK\"
      }
    ],
    \"max_tokens\": 10
  }")

if [ "$HTTP_CODE" != "200" ]; then
    echo ""
    echo "NVIDIA API TEST FAILED"
    echo ""
    cat /tmp/nvidia_test.json
    exit 1
fi

echo ""
echo "NVIDIA API OK"

cat /tmp/nvidia_test.json

# -----------------------------
# LAUNCH OPENCLAW
# -----------------------------

echo ""
echo "[7/7] Launching OpenClaw..."

echo ""
echo "========================================"
echo "INSTALL COMPLETE"
echo "========================================"
echo ""
echo "Run:"
echo ""
echo "openclaw"
echo ""
echo "Then inside OpenClaw try:"
echo ""
echo "hello"
echo ""
echo "or:"
echo ""
echo "Create a Python hello world script"
echo ""
echo "========================================"
#!/bin/bash
# Claude Code 配置 MiniMax API 的脚本
# 用法: bash scripts/setup_claude_minimax.sh [YOUR_MINIMAX_API_KEY]
# 若不传 API Key，将使用占位符 MINIMAX_API_KEY，需手动替换

set -e

# 获取 API Key（可选参数）
API_KEY="${1:-MINIMAX_API_KEY}"

# 根据系统确定路径
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    CLAUDE_DIR="${USERPROFILE}/.claude"
    CLAUDE_JSON="${USERPROFILE}/.claude.json"
else
    CLAUDE_DIR="${HOME}/.claude"
    CLAUDE_JSON="${HOME}/.claude.json"
fi

echo "=== Claude Code MiniMax 配置脚本 ==="
echo "Claude 配置目录: ${CLAUDE_DIR}"
echo "Claude JSON 文件: ${CLAUDE_JSON}"
echo ""

# Step 1: 创建 ~/.claude 目录并写入 settings.json
mkdir -p "${CLAUDE_DIR}"

SETTINGS_FILE="${CLAUDE_DIR}/settings.json"
cat > "${SETTINGS_FILE}" << EOF
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://api.minimaxi.com/anthropic",
    "ANTHROPIC_AUTH_TOKEN": "${API_KEY}",
    "API_TIMEOUT_MS": "3000000",
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": 1,
    "ANTHROPIC_MODEL": "MiniMax-M2.5",
    "ANTHROPIC_SMALL_FAST_MODEL": "MiniMax-M2.5",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "MiniMax-M2.5",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "MiniMax-M2.5",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "MiniMax-M2.5"
  }
}
EOF

echo "✓ 已写入 ${SETTINGS_FILE}"

# Step 2: 创建或更新 .claude.json
if [[ -f "${CLAUDE_JSON}" ]]; then
    # 若文件存在，合并 hasCompletedOnboarding（使用 jq 若可用）
    if command -v jq &> /dev/null; then
        jq '. + {"hasCompletedOnboarding": true}' "${CLAUDE_JSON}" > "${CLAUDE_JSON}.tmp"
        mv "${CLAUDE_JSON}.tmp" "${CLAUDE_JSON}"
    else
        echo '{"hasCompletedOnboarding": true}' > "${CLAUDE_JSON}"
    fi
else
    echo '{"hasCompletedOnboarding": true}' > "${CLAUDE_JSON}"
fi

echo "✓ 已写入 ${CLAUDE_JSON}"
echo ""
echo "=== 配置完成 ==="
if [[ "${API_KEY}" == "MINIMAX_API_KEY" ]]; then
    echo "⚠ 提示: 请将 ${SETTINGS_FILE} 中的 MINIMAX_API_KEY 替换为您的实际 API Key"
fi

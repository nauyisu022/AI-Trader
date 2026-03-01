# Reproducibility Study of AI-Trader

How to reproduce our two experiments: a multi-model benchmark and a news tool ablation study.

**Paper**: [AI-Trader: Benchmarking Autonomous Agents in Real-Time Financial Markets](https://arxiv.org/abs/2512.10971)  
**Original repo**: [HKUDS/AI-Trader](https://github.com/HKUDS/AI-Trader)  
**Presentation**: [Video Link](https://drive.google.com/file/d/14zsNpNgHkB6jrT-87X-2fMc2w44-Tu6c/view?usp=sharing)

---


## Setup

### One-Click Installation

```bash
# 1. Clone project
git clone https://github.com/nauyisu022/AI-Trader.git
cd AI-Trader

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment variables
cp .env.example .env
# Edit .env file and fill in your API keys
```

### Environment Configuration

Create `.env` file and configure the following variables:

```bash
# AI Model API Configuration
OPENAI_API_BASE=https://api.deepseek.com/v1
OPENAI_API_KEY=your_openai_key

# Data Source Configuration
ALPHAADVANTAGE_API_KEY=your_alpha_vantage_key
JINA_API_KEY=your_jina_api_key

# System Configuration
RUNTIME_ENV_PATH=./runtime_env.json

# Service Port Configuration
MATH_HTTP_PORT=8000
SEARCH_HTTP_PORT=8001
TRADE_HTTP_PORT=8002
GETPRICE_HTTP_PORT=8003
CRYPTO_HTTP_PORT=8005

# AI Agent Configuration
AGENT_MAX_STEP=30
```

### Quick Start with Scripts

We provide convenient shell scripts in the `scripts/` directory for easy startup:

```bash
# One-click startup (complete workflow)
bash scripts/main.sh

# Or run step by step:

# Step 1: Prepare data
cd data
python get_interdaily_price.py
python merge_jsonl.py
cd ..

# Step 2: Start MCP services
python agent_tools/start_mcp_services.py

# Step 3: Run trading agent (edit config path as needed)
python main.py configs/default_hour_config.json
```

If MCP service ports are occupied from a previous run:

```bash
lsof -ti:8000,8002,8003,8004,8005 | xargs kill
```

---

## Experiment 1: Multi-Model Benchmark

A unified benchmark of 7 models on the same evaluation window (US market, NASDAQ 100, hourly trading, October 2025).

### Config examples

**DeepSeek-v3.2** (`configs/deepseek_v3.2_hour_config.json`):

```json
{
  "agent_type": "BaseAgent_Hour",
  "market": "us",
  "date_range": {
    "init_date": "2025-10-01 10:00:00",
    "end_date": "2025-10-31 15:00:00"
  },
  "models": [
    {
      "name": "deepseek-chat",
      "basemodel": "deepseek-chat",
      "signature": "deepseek-chat-v3.2",
      "enabled": true
    }
  ],
  "agent_config": {
    "max_steps": 30,
    "max_retries": 3,
    "base_delay": 1.0,
    "initial_cash": 10000.0
  },
  "log_config": { "log_path": "./data/agent_data" }
}
```

**MiniMax-M2.5** (`configs/minimax_config.json`):

```json
{
  "agent_type": "BaseAgent_Hour",
  "market": "us",
  "date_range": {
    "init_date": "2025-10-01 10:00:00",
    "end_date": "2025-10-31 23:00:00"
  },
  "models": [
    {
      "name": "minimax-m2.5",
      "basemodel": "minimax/minimax-m2.5",
      "signature": "minimax-m2.5",
      "enabled": true
    }
  ],
  "agent_config": {
    "max_steps": 30,
    "max_retries": 3,
    "base_delay": 1.0,
    "initial_cash": 10000.0
  },
  "log_config": { "log_path": "./data/agent_data" }
}
```

### Run

```bash
python main.py configs/deepseek_v3.2_hour_config.json
python main.py configs/minimax_config.json
```

### Evaluate

```bash
# DeepSeek-v3.2
python tools/calculate_metrics.py \
  --position-file data/agent_data/deepseek-chat-v3.2/position/position.jsonl \
  --price-file data/merged.jsonl \
  --is-hourly

# MiniMax-M2.5
python tools/calculate_metrics.py \
  --position-file data/agent_data/minimax-m2.5/position/position.jsonl \
  --price-file data/merged.jsonl \
  --is-hourly

# Paper models (truncate to October for fair comparison)
python tools/calculate_metrics.py \
  --position-file data/agent_data/deepseek-chat-v3.1/position/position.jsonl \
  --price-file data/merged.jsonl \
  --is-hourly \
  --start-date "2025-10-01" \
  --end-date "2025-10-31"
```

## Experiment 2: News Tool Ablation

Compare trading performance with and without the news search tool. Same model, same period, same capital — only the news tool availability differs.

### Run baseline (with news)

```bash
python main.py configs/test_deepseek_official_api.json
```

### Run ablation (without news)

```bash
python main.py configs/deepseek_v3.2_no_news_config.json
```

The only difference in the ablation config:

```json
"agent_config": {
  "disabled_tools": ["search"]
}
```

---

## Code Changes from Original Repo

### 1. Per-model API configuration

The original code uses a single global `OPENAI_API_BASE` / `OPENAI_API_KEY`. We added per-model `openai_base_url` and `openai_api_key` fields in the config JSON so that DeepSeek and MiniMax can use different endpoints without changing `.env`.

**Files changed**: `main.py`

### 2. DeepSeek official API compatibility

The original authors used an OpenRouter proxy. The native DeepSeek API returns tool-call responses in a different message structure. We created `DeepSeekChatOpenAI`, a custom `ChatOpenAI` wrapper that handles:
- `tool_calls.args` returned as JSON strings instead of dicts
- Message `content` returned as lists instead of strings

**Files changed**: `tools/model_factory.py`

### 3. Ablation infrastructure (`disabled_tools`)

We added a `disabled_tools` parameter to all agent constructors. It filters out specified MCP tool servers before the agent starts trading.

**Files changed**: `agent/base_agent/base_agent.py`, `agent/base_agent_astock/base_agent_astock.py`, `agent/base_agent_crypto/base_agent_crypto.py`, `main.py`

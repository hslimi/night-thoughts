---
title: "Building an AI Trading Team on Your Mac: A Deep Dive into TradingAgents with Gemini 3"
datePublished: 2026-10-10T07:47:29.044Z
cuid: cmv23d6r6000106kzewr5hjim
slug: building-an-ai-trading-team-on-your-mac-a-deep-dive-into-tradingagents-with-gemini-3
tags: ai, python, trading, llm, langchain

---

## Introduction

TradingAgents is an open-source multi-agent LLM framework that simulates a real-world trading firm. It deploys specialized agents — fundamental analysts, sentiment experts, technical analysts, researchers, traders, and risk managers — that collaboratively evaluate market conditions and debate optimal strategies before producing a final trading decision.

Built on **LangGraph** for stateful orchestration, the framework supports multiple LLM providers including Google Gemini, OpenAI, Anthropic, and more. This guide walks you through a complete production-grade setup on a Mac Mini M5: **Gemini 3** as the inference backend, **LangGraph Studio** for visual debugging, **uv** for Python environment management, and **yfinance** for market data.

**What you'll build:**
- A Python 3.11 virtual environment managed by `uv`
- TradingAgents with Gemini 3 Pro and Gemini 3 Flash
- LangGraph Studio for step-by-step visual debugging
- Checkpoint/resume support so long analyses survive interruptions
- A first live analysis run on a ticker of your choice


## Architecture: How the Virtual Trading Firm Works

TradingAgents mirrors a real trading firm's organizational structure, implemented as a LangGraph `StateGraph` where each agent is a node and edges define information flow.

**Four-layer workflow:**

| Layer | Agents | Role | Think Level |
|-------|--------|------|-------------|
| **Analyst Team** | Fundamentals, Sentiment, News, Technical | Gather data, produce initial reports | Quick Think |
| **Researcher Debate** | Bull Researcher ↔ Bear Researcher | Structured debate on analyst findings | Deep Think |
| **Trading** | Trader Agent | Composes reports into a trading plan | Deep Think |
| **Risk Management** | Aggressive ↔ Conservative ↔ Neutral Analyst, Portfolio Manager | Debates risk, approves/rejects the trade | Deep Think |

Each analyst runs a conditional tool-call loop: the agent calls a data tool (e.g., `get_stock_data`), receives the result, loops back, and advances when it has enough data. The debate phase uses bidirectional loops — Bull and Bear researchers alternate until the debate count reaches `2 × max_debate_rounds`. The risk phase rotates three analysts until `3 × max_risk_discuss_rounds`.

**What runs where:**

| Layer | Location | Description |
|-------|----------|-------------|
| LangGraph orchestration | **Local** (Mac Mini) | State graph compilation, node routing, checkpoint persistence |
| TradingAgents framework | **Local** | Agent definitions, tool nodes, memory logs |
| yfinance data fetching | **Local** (network) | HTTP requests to Yahoo Finance APIs |
| Gemini inference | **Remote** (Google Cloud) | The actual LLM reasoning — each agent node sends a prompt to Gemini |

When you call `ta.propagate("NVDA", date)`, LangGraph compiles the graph locally, then streams execution node by node. Each agent node makes a remote API call to Gemini for reasoning, merges the response back into the shared `AgentState`, and LangGraph routes to the next node based on conditional logic.


## Why Gemini 3

**Native Google client support.** TradingAgents has a dedicated `GoogleClient` that handles Gemini's unique content format — Gemini 3 models return content as a list of typed blocks rather than plain strings, and the client normalizes this so downstream agents don't break.

**Thinking level control.** Gemini 3 models support `thinking_level` parameters (`low`, `high`, and `minimal` for Flash models), letting you control the reasoning budget per role. The `GoogleClient` maps these to the appropriate API parameters based on the model.

**Single-provider simplicity.** Using Gemini for both Quick Think and Deep Think roles avoids cross-provider routing bugs that can cause API key mismatches or silent fallbacks.

**Model selection for this project:**

- **Deep Think** — `gemini-3.8-flash` : Our most intelligent Flash model, engineered for long-horizon software engineering, autonomous agents, and complex enterprise workflows. Used for the Researcher debate, Trader, and Risk Management agents.
- **Quick Think** — `gemini-3.1-flash-lite` : Frontier-class performance rivaling larger models at a fraction of the cost. Used for the four Analyst agents, which are high-throughput data gathering tasks.


## Step-by-Step Setup

### Step 1: Install Homebrew

If you don't have Homebrew:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**Expected result:** Installation completes with a message about adding Homebrew to your PATH. Follow the printed instructions for your shell (zsh on macOS).

Verify:

```bash
brew --version
```

**Expected output:**
```
Homebrew 4.x.x
```

### Step 2: Install uv

```bash
brew install uv
```

**Expected result:** uv installs via Homebrew.

Verify:

```bash
uv --version
```

**Expected output:**
```
uv 0.x.x
```

### Step 3: Clone TradingAgents and Create the Environment

```bash
git clone https://github.com/TauricResearch/TradingAgents.git
cd TradingAgents
uv venv --python 3.11
```

**Expected result:**
```
Using CPython 3.11.x
Creating virtual environment at: .venv
Activate with: source .venv/bin/activate
```

**Note:** `uv` will automatically download Python 3.11 if it's not already on your system.

Activate the environment:

```bash
source .venv/bin/activate
```

**Expected result:** Your shell prompt changes to show `(.venv)`.

### Step 4: Install TradingAgents and LangGraph Studio

For the official LangGraph installation reference, see the [LangGraph install documentation](https://docs.langchain.com/oss/python/langgraph/install). For the CLI and Studio setup, see the [LangGraph CLI documentation](https://docs.langchain.com/langsmith/cli) and the [Studio quickstart](https://docs.langchain.com/langsmith/quick-start-studio).

```bash
uv pip install -e .
uv pip install -U "langgraph-cli[inmem]"
```

**Expected result:** Both installations complete without errors. The `-e` flag installs TradingAgents in editable mode, so changes to the source code take effect immediately.

Verify the installation:

```bash
python -c "from tradingagents.graph.trading_graph import TradingAgentsGraph; print('TradingAgents OK')"
python -c "from langgraph.graph import StateGraph; print('LangGraph OK')"
```

**Expected output:**
```
TradingAgents OK
LangGraph OK
```

### Step 5: Configure the Environment

Create the `.env` file:

```bash
vim .env
```

Paste the following:

```bash
# --- LLM Provider ---
TRADINGAGENTS_LLM_PROVIDER=google

# --- API Key ---
GOOGLE_API_KEY=your-google-api-key-here

# --- Models ---
TRADINGAGENTS_DEEP_THINK_LLM=gemini-3.8-flash
TRADINGAGENTS_QUICK_THINK_LLM=gemini-3.1-flash-lite

# --- Data Vendors ---
TRADINGAGENTS_DATA_DIR=./trading_data
LOG_LEVEL=INFO
```

Save and exit: press `Esc`, type `:wq`, press `Enter`.

**Expected result:** `.env` file created with your configuration.

**Replacing your API key:** Edit the file again with `vim .env` and replace `your-google-api-key-here` with your actual key from [Google AI Studio](https://aistudio.google.com/apikey).

### Step 6: Create the Verification Script

```bash
vim verify_setup.py
```

Paste:

```python
import os
import requests
from dotenv import load_dotenv
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

load_dotenv()

# --- Step 1: Direct Gemini API verification (actual network call) ---

google_key = os.getenv("GOOGLE_API_KEY")
if not google_key:
    print("GOOGLE_API_KEY not set")
    exit(1)

quick_model = os.getenv("TRADINGAGENTS_QUICK_THINK_LLM")

try:
    resp = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{quick_model}:generateContent",
        headers={"x-goog-api-key": google_key},
        json={
            "contents": [{"parts": [{"text": "ping"}]}],
            "generationConfig": {"maxOutputTokens": 1}
        },
        timeout=60
    )
    resp.raise_for_status()
    print("Gemini endpoint verified")
except Exception as e:
    print(f"Gemini failed: {e}")
    exit(1)

# --- Step 2: Graph initialization ---

config = DEFAULT_CONFIG.copy()
config["llm_provider"] = "google"
config["quick_think_llm"] = quick_model
config["deep_think_llm"] = os.getenv("TRADINGAGENTS_DEEP_THINK_LLM")

config["data_vendors"] = {
    "core_stock_apis": "yfinance",
    "technical_indicators": "yfinance",
    "fundamental_data": "yfinance",
    "news_data": "yfinance"
}

config["max_debate_rounds"] = 1

print("Initializing Graph...")
ta = TradingAgentsGraph(debug=True, config=config)
print("Graph initialized successfully.")
print("\nALL CHECKS PASSED. Ready to execute full trade.")
```

Save and exit.

Run:

```bash
python verify_setup.py
```

**Expected output:**
```
Gemini endpoint verified
Initializing Graph...
Graph initialized successfully.

ALL CHECKS PASSED. Ready to execute full trade.
```

**Important:** This script makes a real API call to Gemini — not just object construction. If the Gemini endpoint is unreachable or your key is invalid, it fails immediately with a clear error.

### Step 7: Create the Trade Runner Script

```bash
vim trade.py
```

Paste:

```python
import os
from datetime import date
from dotenv import load_dotenv
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

load_dotenv()

config = DEFAULT_CONFIG.copy()
config["llm_provider"] = "google"
config["quick_think_llm"] = os.getenv("TRADINGAGENTS_QUICK_THINK_LLM")
config["deep_think_llm"] = os.getenv("TRADINGAGENTS_DEEP_THINK_LLM")
config["data_vendors"] = {
    "core_stock_apis": "yfinance",
    "technical_indicators": "yfinance",
    "fundamental_data": "yfinance",
    "news_data": "yfinance"
}
config["max_debate_rounds"] = 2

ta = TradingAgentsGraph(debug=True, config=config)

ticker = "NVDA"
today = date.today().isoformat()
print(f"Starting Analysis for {ticker} ({today})...")

state, decision = ta.propagate(ticker, today)

print("\n" + "="*60)
print("FINAL DECISION:")
print("="*60)
print(decision)
```

Save and exit.

Run:

```bash
python trade.py
```

**Expected result:** The graph executes node by node. You'll see analyst reports being generated, the bull/bear debate unfold, and finally the portfolio manager's decision printed to the terminal. A full run with `max_debate_rounds = 2` typically takes 3–8 minutes depending on Gemini's response latency.

### Step 8: Enable Checkpoint/Resume

TradingAgents supports `--checkpoint` to save state after each node to a per-ticker SQLite database. If a run crashes, it resumes from the last successful node instead of restarting.

**How it works:** Each ticker's run is stored in its own SQLite database at `~/.tradingagents/cache/checkpoints/<TICKER>.db`. The `thread_id` is deterministic, based on the ticker, date, and a signature hash of graph-shape-affecting choices (such as the selected analysts or asset type). This ensures that if you change the configuration in a way that alters the graph's structure, a new checkpoint thread ID is generated, preventing resumption from an incompatible prior state.

To enable checkpointing in your `trade.py`, add the `checkpoint` flag to the config:

```python
config["checkpoint_enabled"] = True
```

Then, on resume, the framework prints `Resuming from step N for <TICKER> on <date>` instead of restarting from scratch. After a successful completion, the checkpoint is automatically cleaned up.

**CLI alternative:** If you use the TradingAgents CLI, pass `--checkpoint` as a command-line argument.


## LangGraph Studio: Visual Debugging

LangGraph Studio gives you a live, interactive view of the graph as it executes. You can set breakpoints, inspect state at any node, view exact prompts sent to Gemini, and debug failures without re-running the entire pipeline. For the official reference, see the [LangGraph Studio documentation](https://docs.langchain.com/langsmith/quick-start-studio).

### Setup

Create `langgraph.json` at the repo root:

```bash
vim langgraph.json
```

Paste:

```json
{
  "dependencies": ["."],
  "graphs": {
    "trading_agents": {
      "path": "tradingagents/graph/trading_graph.py:TradingAgentsGraph",
      "config": {
        "debug": true
      }
    }
  },
  "env": ".env"
}
```

Save and exit.

Start the dev server:

```bash
langgraph dev
```

**Expected output:**
```
Server started at http://localhost:2024
```

Open Studio in your browser. Safari and Brave block plain HTTP on localhost — if you're using either, add the `--tunnel` flag to get an HTTPS-accessible endpoint.

### What Studio Gives You

| Feature | What It Does |
|---------|--------------|
| **Interactive graph visualization** | See all nodes and edges rendered as a live graph |
| **Step-by-step execution** | Pause at any node, inspect input state, then resume |
| **State inspection** | View the full `AgentState` at any point — messages, reports, debate counts |
| **Breakpoints** | Set breakpoints on specific nodes to halt execution |
| **Prompt & tool debugging** | View exact prompts sent to Gemini, tool arguments, token usage, latency |
| **State editing & re-run** | Modify state at a breakpoint and re-run from that point |
| **LangSmith integration** | Import traced runs from production for debugging |

### Debugging Workflow: A Practical Example

**Step 1: Launch and load the graph.** Open Studio. You'll see the full TradingAgents graph rendered — Market Analyst, Social Media Analyst, News Analyst, Fundamentals Analyst, Bull Researcher, Bear Researcher, Research Manager, Trader, and the Risk Analysts.

**Step 2: Run a test input.** In the input panel, provide:

```json
{
  "company_of_interest": "NVDA",
  "trade_date": "2026-10-10",
  "messages": []
}
```

Click **Run**. Studio begins executing node by node, highlighting the current node.

**Step 3: Inspect state at each node.** When execution pauses at the Market Analyst node (if you set a breakpoint), click **Inspect State**. You'll see the `AgentState` with all fields: `messages`, `company_of_interest`, `trade_date`, `market_report`, `sentiment_report`, `news_report`, `fundamentals_report`, `investment_debate_state` (with `bull_history`, `bear_history`, `count`), and `risk_debate_state`.

**Step 4: Check tool calls and prompts.** Click the **Trace** tab to see the exact prompt sent to Gemini for this node — system prompt, user message, tool definitions, and the model's response.

**Step 5: Debug a failure.** If the Bull Researcher node fails with a Gemini API error (e.g., rate limit), Studio captures the exception with full context. You can inspect the input state at the failure point, modify the state (e.g., adjust `max_debate_rounds` or swap the model), and re-run from that point.

**Step 6: Attach a line-level debugger (optional).** For breakpoints and variable inspection:

```bash
uv pip install debugpy
langgraph dev --debug-port 5678
```

Then attach VS Code or PyCharm to port 5678.


## Data Vendors: yfinance and Alternatives

TradingAgents ships with **yfinance** as the default data vendor. It requires no API keys and covers core stock APIs, technical indicators, fundamentals, and news.

**Configuration:**

```python
config["data_vendors"] = {
    "core_stock_apis": "yfinance",
    "technical_indicators": "yfinance",
    "fundamental_data": "yfinance",
    "news_data": "yfinance"
}
```

**Supported alternatives:**

| Vendor | Category | API Key Required | Notes |
|--------|----------|-----------------|-------|
| `alpha_vantage` | Core stock, fundamentals | Yes | Free tier: 25 requests/day |
| `sec_edgar` | Fundamentals | No | SEC asks callers to identify themselves |
| `fred` | Macro data | Yes | Federal Reserve economic data |
| `polymarket` | Prediction markets | No | Optional enrichment category |

To switch vendors, replace the value in the `data_vendors` dict:

```python
config["data_vendors"]["core_stock_apis"] = "alpha_vantage"
config["data_vendors"]["fundamental_data"] = "sec_edgar,yfinance"
```

You can specify comma-separated fallback chains. If the first vendor is unavailable, the system automatically tries the next in the chain.


## Risks and Limitations

| Risk | Severity | Mitigation |
|------|----------|------------|
| **Gemini rate limits** | High | Free tier is 15 RPM. A single trade run can exceed this. Enable billing or throttle with `max_debate_rounds = 1` |
| **yfinance single point of failure** | Medium | Web scraping tool, subject to Yahoo page changes. Use fallback chains |
| **Context growth during debate** | Medium | Set `max_debate_rounds` and `max_risk_discuss_rounds` conservatively for long runs |
| **Checkpoint SQLite contention** | Low | Per-ticker databases prevent contention. Enabled via `--checkpoint` |

**Important disclaimer:** TradingAgents is designed for research purposes. Trading performance may vary based on many factors, including the chosen backbone language models, model temperature, trading periods, and data quality. It is not intended as financial, investment, or trading advice.


## Conclusion

You now have a fully operational multi-agent trading firm running on your Mac Mini M5. The architecture is:

- **LangGraph** runs locally, orchestrating the entire workflow
- **Gemini 3** provides remote inference — `gemini-3.8-flash` for deep reasoning, `gemini-3.1-flash-lite` for high-throughput analysts
- **yfinance** fetches market data with no API keys required
- **LangGraph Studio** gives you step-by-step visual debugging
- **Checkpoint/resume** ensures long analyses survive interruptions

**Next steps:**
- Experiment with different Gemini model combinations for Quick Think and Deep Think
- Add fallback data vendors (SEC EDGAR for fundamentals, Alpha Vantage for stock data)
- Integrate with the Telegram bot wrapper for remote triggering
- Add a local Ollama model for offline capability
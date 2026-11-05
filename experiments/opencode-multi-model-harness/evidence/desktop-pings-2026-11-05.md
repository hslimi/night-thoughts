# Desktop pings, 2026-11-05

OpenCode Desktop 2.2.5. Prompt: `Reply with exactly one word: pong`. Each row is a new session, with the model chosen in the Desktop model picker. Models and errors come from the session exports. A reply shows that the route answers; it does not test tools, reasoning, attachments or failover.

## With the Best fallback file active

| Selected model | Result |
|---|---|
| `anthropic/claude-haiku-5-5` | Replied `pong` |
| `openrouter/anthropic/claude-haiku-5.5` | Replied `pong` |
| `opencode/glm-5.3-flash-free` | `429 provider.free-limit`, then the plugin failed over to `openrouter/anthropic/claude-sonnet-5.5`, which replied `pong` at $0.0316 |

The GLM row is a failover, not a GLM reply. The Desktop showed `pong` as if the free model had answered. The session export and `opencode-fallback.log` show what happened. See `glm-free-limit-failover.session.json`.

## With the fallback plugin disabled (`"enabled": false`)

| Selected model | Result |
|---|---|
| `opencode/deepseek-v4.1-flash-free` | `429 provider.free-limit` |
| `opencode/nemotron-3.5-super-vl-free` | `429 provider.free-limit` |
| `openrouter/nvidia/nemotron-3.5-super-vl` (paid) | Replied `pong` at $0.00155 |
| `openrouter/nvidia/nemotron-3.5-super-vl:free` | Replied `pong` at $0. It had to be switched on first under Manage models in the picker |

Error text from the provider: `Free usage limit reached. Connect a provider or subscribe to OpenCode Go to keep going, or switch models.`

No OpenCode Console account was connected.

## Revised Cheap candidates, fallback plugin disabled

After the free limit, the Cheap chains were redrawn around low-cost open-weight models on OpenRouter and DeepSeek direct. Each OpenRouter model had to be switched on under Manage models first.

| Selected model | Result |
|---|---|
| `openrouter/qwen/qwen3.6-35b-a3b` | Replied `pong` at $0.00099 |
| `openrouter/qwen/qwen3.8-27b` | Replied `pong` at $0.00062 |
| `openrouter/deepseek/deepseek-v4.1-flash` | Replied `pong` at $0.00085 |
| `openrouter/z-ai/glm-5.3-flash` | Replied `pong` at $0.00097 |
| `deepseek/deepseek-flash` | First check: balance $0.00, `is_available: false`, so not sent. After a $5 top-up: replied `pong` at $0.001245. The picker labels it `DeepSeek V4.1 Flash 1017` |

## What this leaves open

- The free-limit error carried `retryAfterMs: 34735000`, about 9.6 hours, which points to a reset around 2026-11-06 00:21 UTC. The limit's size and scope are not documented, and the retry has not been tried yet.
- This machine's earlier `opencode/` usage in the 30-day stats was small: 6 DeepSeek steps and 1 Big Pickle step, about 16K input tokens. So the limit may be low or shared more widely than this machine. That is not established.
- Whether signing in to OpenCode Console changes the limit is not documented and has not been tested.
- Because the three `opencode/` free routes failed, those chains were dropped. `config/cheap/` holds the revised chains, which have not been activated. Every route in them has now replied to a one-word ping; nothing beyond that has been tested.

## Failed attempts

- The first Cheap pings never sent a prompt: the automation looked in the wrong picker section, and then expected a `Provider / Model` label that OpenCode's own models do not show.
- The automation initially recorded the GLM failover as a successful GLM reply. The unexpected $0.03 charge on a free model exposed the error.
- The DeepSeek and Nemotron free-route pings timed out in the automation because it did not recognise the free-limit wording. The session exports show the real error.
- The test of pinning the OpenRouter backup to a specific upstream did not run, because the automation could not select the model. OpenCode exports contain no OpenRouter generation IDs, so they cannot show which upstream served a request.

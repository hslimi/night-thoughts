# Acceptance protocol results

OpenCode Desktop 2.2.5 on macOS, opencode-model-router 2.9.1, opencode-runtime-fallback 0.3.1. Date: 2026-11-05 and 2026-11-06. Tests ran from the Desktop UI. Costs are OpenCode's figures and have not been reconciled with provider dashboards.

## Best

| # | Test | Result | Cost | Notes |
|---|---|---|---:|---|
| 1 | Startup: `/tiers`, `/router`, `plugin list` | Pass | $0.0023 | Correct preset and models; both plugins listed. These commands go through the model, so they cost a little |
| 2 | Image with a random code | Pass | $0.0002 | Exact code returned on Haiku direct |
| 3 | Native PDF, code on page 2 | Pass | $0.0007 | Exact code and page returned on Haiku direct |
| 4 | Routing | Pass | $0.25 | See notes |
| 5 | 429 after a completed tool result | Pass | $0.0023 | Same session; backup identified; no duplicate work |
| 6 | No first token | Pass | $0.0001 | Timeout set to 20 s for the test; backup replied, 38 s in total |
| 7 | Capability after failover | Partial | $0.0034 | Image and tools pass. PDF answer correct, but see notes |
| 8 | Memory: fresh session and resume | Pass | Under $0.01 | Codename from `AGENTS.md` with no tools; resumed session recalled its objective |
| 9 | Semantic memory | Out of scope | | Tried, then dropped. The memory tool was not reliably available. See notes |
| 10 | Compaction | Pass | Under $0.01 | Objective, decision and next action survived `/compact` |
| 11 | Swarm bounds | Pass | Under $0.01 | Two subagents as requested, none nested. Router roles mode not tested |
| 12 | Permissions | Pass | Under $0.01 | See notes |
| 13 | Recovery | Pass | Under $0.01 | Rewind removed the file and restored the prompt; Redo reapplied it |
| 14 | Cost reconciliation | Not finished | | Route-switch cost measured; dashboards not yet compared |

### Notes

**Test 4.** A one-file lookup stayed with the Sonnet orchestrator, which matches the router's "skip delegation for trivial work" rule. A larger exploration in a clean clone went to a subagent, and Haiku did the reading (3 steps, $0.0026). The edit went to a Sonnet subagent, and `node --test` passed 2 of 2. The architecture question reached Opus through a subagent.

**`/router stats` does not exist in 2.9.1.** The router treated `stats` as unknown input and printed its help. Per-model use came from `opencode stats --models --cost --json`.

**Test 5.** The mock provider wrote `notes.txt` through a tool call, then returned 429. Haiku continued in the same session and edited the existing file rather than starting again. `notes.txt` was written once, and the backup then corrected its text to match the prompt.

**Also tested:** a 503 from the mock failed over the same way (`05b-503`).

**Test 7.** With tools forbidden and no failover, `openrouter/anthropic/claude-haiku-5.5` read an attached PDF natively: 4,796 input tokens and the exact code. After a failover, the same route returned the correct code, but the first request carried almost no PDF tokens and it delegated to a subagent. So the PDF may not reach the backup natively after a failover. The token counts suggest this; it is not confirmed. The image and a tool call did work on that backup.

**Test 9, why semantic memory was dropped.** `opencode-supermemory` 2.1.1 was tried against a self-hosted `supermemory-server` 0.0.9 and a local model served by oMLX. When the agent had the memory tool, it worked: Best passed save and correct in one run, and Cheap passed save, correct and delete in another. No setup passed all four checks in one run, because the tool was often missing from the session. That happened with per-project and global plugin config, and after a full restart. `plugin list` did not predict it. Without the tool, one model wrote its own `MEMORY.md` as a substitute. The server stayed on local connections once its embedding model had downloaded from Hugging Face, though one early address, `35.181.67.163`, was never identified. The server is closed source.

**Test 12.** `git status` ran without a prompt. `git push --dry-run` and `rm -rf build` were denied without a prompt. A `.env` read and `ls src` each asked first, and both were denied by choice. HEAD did not move.

**Test 13.** `/undo` and `/redo` are not slash commands in this Desktop build. Rollback is **Rewind to here** on a message or **Undo** in the command palette, and **Redo** is in the palette.

**Test 14, route switch.** Same model and session, Haiku 5.5:

| Turn | Route | Cache read | Cache write | Cost |
|---|---:|---:|---:|---:|
| 1 | Anthropic | 14,141 | 83 | $0.000154 |
| 2 | Anthropic | 14,224 | 16 | $0.000146 |
| 3 (switched) | OpenRouter | 1,595 | 12,666 | $0.001601 |
| 4 | OpenRouter | 14,261 | 16 | $0.000147 |
| 5 (switched back) | Anthropic | 14,240 | 48 | $0.000150 |

The switch cost about 11 times a normal turn, once, as a cache write rather than full input price. Switching back stayed cheap because the first cache was still warm.

## Cheap

Chains: `deepseek/deepseek-flash` on fast, `openrouter/qwen/qwen3.6-35b-a3b` on medium, `openrouter/qwen/qwen3.8-27b` on heavy.

| # | Test | Result | Cost | Notes |
|---|---|---|---:|---|
| 1 | Startup | Pass | $0.0014 | `cheap-open` preset with the right models |
| 2 | Image | Pass | $0.0011 | Exact code on Qwen 3.6 |
| 3 | PDF: local text plus page image | Pass | $0.0014 | Exact code, page reported as "Second page" |
| 4 | Routing, first run | Fail | $0.004 | Qwen 3.6 orchestrator never delegated. See notes |
| 4 | Routing, with orchestrator rule and GLM-5.3-Flash | Pass | About $0.02 | Exploration to DeepSeek, edit to Qwen 3.6, architecture to Qwen 3.8 |
| 5 | 429 after a completed tool result | Pass | $0.0014 | Same session; `deepseek/deepseek-flash` took over, read the file and corrected the text |
| 6 | No first token | Pass | $0.0001 | Timeout set to 20 s for the test; 38 s in total |
| 7 | Image and tools after failover | Pass | $0.0016 | `deepseek/deepseek-flash` read the image and called `read` |
| 8 | Memory: fresh session and resume | Pass | Under $0.01 | On GLM: codename from `AGENTS.md` with no tools; resumed session recalled its objective |
| 10 | Compaction | Pass | Under $0.01 | Objective, decision and next action survived |
| 11 | Swarm bounds | Pass | Under $0.01 | On GLM with the rule: two subagents as requested, none nested. One run |

**Test 4, why Qwen did not delegate.** Two local capture models sent the same prompt, differing only in name, and OpenCode's requests were compared. Both received the router's "Model Delegation Protocol (MANDATORY)" and the same tools, including `subagent`. Only the model with `claude-` in its name also received a forceful opener: dispatch rather than execute, with at most 2 direct read-only calls per turn. The router chooses this by model name. In the first run, Qwen 3.6's reasoning never mentioned delegating.

**Test 4, the fix.** `config/cheap/AGENTS.orchestrator-rule.md` adds an equivalent rule through `AGENTS.md`. Results with the rule:

| Orchestrator | Exploration | Edit | Architecture |
|---|---|---|---|
| Qwen 3.6 | Delegated in one run; direct in a smaller two-file run, which the 2-read allowance permits | Delegated | Answered itself in one run; reached Qwen 3.8 in another |
| GLM-5.3-Flash | To DeepSeek | To Qwen 3.6 | To Qwen 3.8 |
| DeepSeek V4.1 Flash | Subagent errors, then did it itself | To Qwen 3.6 | Stopped at a permission prompt, not finished |

Each cell is one or two runs. GLM is the best result here, not proof that it always routes correctly.

The rule also worked from `~/.config/opencode/AGENTS.md`, in a project with no rule of its own (`cheap/04f-routing-global-rule`). With GLM, the edit went to Qwen 3.6 and tests passed 2 of 2; a two-file exploration stayed direct, within the 2-read allowance; and Qwen 3.8 ran for the architecture question.

**GLM's output cap.** GLM-5.3-Flash advertises 943,717 output tokens and `deepseek-flash` 393,216, which would fail DeepSeek as GLM's first backup. `config/cheap/opencode.jsonc` caps GLM at 393,216 with `limit.output`, and the static check models that cap. A local capture of the actual request showed OpenCode asking for `max_tokens: 256000`, so OpenCode's request stayed below the cap and the cap did not change it. An earlier refusal for a Gemini model with a similar catalog limit also showed 256,000. So the cap makes the contract consistent on paper; it does not reduce what OpenCode reserves.

**Config default.** With GLM set as the root `model`, a new Desktop session still opened on the last model used. Check the picker.

**Denied subagent.** When a read inside a subagent was denied, the whole subagent was cancelled, and the orchestrator carried on by itself.

**Caching.** Qwen 3.6 requests through OpenRouter showed no cached tokens, so its whole prompt was billed at full input price each time. `deepseek-flash` did cache.

**Limited evidence:** Qwen 3.8 has only answered architecture questions, and GLM-5.3-Flash has only orchestrated. Neither has made edits in these tests.

### Best tests not repeated on Cheap, and why

| # | Test | Why |
|---|---|---|
| 12 | Permissions | OpenCode applies these rules before a command runs, whichever model asked |
| 13 | Rewind and Redo | Snapshots are a harness feature and do not involve the model |
| 14 | Cost reconciliation | Dashboard comparison covers Cheap spend too. The route-switch measurement was run on Best only |

## Run conditions

- Best tests 1 to 3 ran on the app's existing profile. All others ran on a clean profile, created with `XDG_DATA_HOME`, `XDG_STATE_HOME` and `--user-data-dir`, because archived sessions cannot be hidden from the sidebar.
- The router plugin raised the first request from about 8,600 to about 14,900 tokens.
- The Desktop was driven with automation. The steps are the same ones a reader would click.

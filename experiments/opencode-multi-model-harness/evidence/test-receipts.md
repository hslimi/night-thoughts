# Test receipts

One receipt per test. Each one says what harness property it checks, how the test was set up, what I sent, what counted as a pass, and how I checked it. The prompts are quoted exactly. Session exports for every run are in `best/` and `cheap/` next to this file; `manifest.md` maps them to tests. Results and notes are in `protocol-results.md`.

"The test repository" is the disposable repository created by `../scripts/create_disposable_repo.sh`. "The mock" is `../scripts/mock_provider.mjs`, a local provider that fails on purpose. The same receipts are the appendix of the article.

### Test 1: Startup

| | |
|---|---|
| **Checks** | Both plugins load, and the router uses the intended preset and models |
| **Why** | If a plugin silently fails to load, routing and failover are missing, and nothing on screen says so |
| **Setup** | Package config in `~/.config/opencode/`, Desktop restarted |
| **Scenario** | Run `opencode-cli plugin list`, then send `/tiers` and `/router` in a new session |
| **Pass if** | Both plugins listed with their pinned versions; `/tiers` shows the package's preset (`best-frontier` or `cheap-open`) and the three tier models exactly as configured |
| **Checked in** | CLI output and the session export |
| **Result** | Best: pass. Cheap: pass |

### Test 2: Image input

| | |
|---|---|
| **Checks** | An attached image reaches the model as an image |
| **Why** | A model that does not receive the image may still give a confident answer |
| **Setup** | A PNG containing only a random code generated for the test |
| **Scenario** | Attach the image and send: "What exact code is shown in this image? Reply with only the code." On Cheap the prompt also said "Do not use tools." |
| **Pass if** | The reply contains the exact code. A guess cannot match it |
| **Checked in** | The session export, compared with the generated code |
| **Result** | Best (Haiku): pass. Cheap (Qwen 3.6): pass |

### Test 3: PDF input

| | |
|---|---|
| **Checks** | A PDF can be read, including where the content is |
| **Why** | Native PDF support differs between models, and Cheap's models do not advertise it |
| **Setup** | A multi-page PDF with a random review code on page 2 only. On Cheap, converted first with `pdftotext` and `pdftoppm`, as in the article's PDF section |
| **Scenario** | Best: attach the PDF and send "This document has a review code. Reply with the exact code and the page number it is on." Cheap: attach the text and page image and send "The text and page image come from one document. Reply with the review code and which page it is on. Do not use tools." |
| **Pass if** | Exact code, and page 2 |
| **Checked in** | The session export; on Best, also the input token count, which shows whether the PDF was actually sent |
| **Result** | Best: pass, natively. Cheap: pass, after local conversion |

### Test 4: Routing

| | |
|---|---|
| **Checks** | The orchestrator sends each kind of work to the right tier |
| **Why** | This is the point of the router. Without it, every request runs on the orchestrator's model and price |
| **Setup** | The test repository, a new session on the package's orchestrator |
| **Scenario** | Three prompts in one session. Exploration on Cheap: "Search the src and test folders and summarise what each file does, with file and line references. Do not change anything." On Best, a one-file lookup ("Where is the add function defined, and which test covers it? Do not change anything."), then a larger exploration of a real repository's `experiments` folder, read only. Edit: "Add a subtract(a, b) function to src/math.mjs with a matching test in test/math.test.mjs, then run node --test and report the result." Architecture: "Architecture question, no edits: if this project grew to many math modules across several packages, compare a single shared package with one package per module, considering versioning and test isolation. Recommend one, briefly." Only the `node --test` prompt was approved; any other permission request stopped the test |
| **Pass if** | Exploration runs on the fast model, the edit on the medium model, and architecture on the heavy model, each through a subagent; the tests pass after the edit |
| **Checked in** | The model that produced each step in the export, and `opencode-cli stats --models --cost` before and after each prompt |
| **Result** | Best: pass, with a small lookup kept by the orchestrator as the router intends. Cheap: **fail** with Qwen 3.6 as orchestrator, then pass with GLM-5.3-Flash and the `AGENTS.md` rule. One or two runs per setup |

### Test 5: Failover after a rate limit

| | |
|---|---|
| **Checks** | When a provider returns `429` mid-task, the backup continues the same task without repeating finished work |
| **Why** | Failing over at the start of a task is easy. Failing over after a tool has already changed a file is where duplicated or lost work happens |
| **Setup** | The mock as the primary, set to make one `write` tool call (creating `notes.txt`) and then return `429`. A real backup: Haiku on Best, DeepSeek Flash on Cheap |
| **Scenario** | "Create notes.txt with the text 'written once'. Then read src/math.mjs and tell me the name of the first exported function." |
| **Pass if** | The backup continues in the **same session** (no new session created); it works on the existing `notes.txt` rather than writing it again; it reads `src/math.mjs`; the export records the switch to the backup model |
| **Checked in** | The export, the fallback plugin's log, the session count before and after, and the file on disk |
| **Result** | Best: pass. Cheap: pass. The mock deliberately wrote slightly different text, and both backups noticed and corrected it |

A second variant used a mock that always returns `503`, with "Reply with exactly one word: pong". Best failed over the same way.

### Test 6: Stalled provider

| | |
|---|---|
| **Checks** | A provider that accepts the request and never answers is cut off, and the backup answers |
| **Why** | A stall is worse than an error: without a timeout the session just hangs |
| **Setup** | The mock accepting the request and sending nothing. Fallback timeout lowered to 20 seconds for the test; the packages use 45 |
| **Scenario** | "Reply with exactly one word: pong" |
| **Pass if** | The backup replies `pong` in the same session, shortly after the timeout |
| **Checked in** | The export and the plugin log, which records the timeout |
| **Result** | Best: pass. Cheap: pass. 38 seconds in total on both |

### Test 7: Capabilities after failover

| | |
|---|---|
| **Checks** | Attachments and tools still work once the backup has taken over. On Best, this test used the OpenRouter backup |
| **Why** | Test 5 shows the backup can continue. This shows it can still read what the primary was given |
| **Setup** | The mock returning `503` as the primary, a backup on the other route, and **new** codes, different from tests 2 and 3, so an earlier answer could not be reused |
| **Scenario** | Image: attach it and send "What exact code is shown in this image? Then read src/math.mjs and name its first exported function." PDF (Best only): attach it and send "This document has a review code. Reply with the exact code and the page number it is on." |
| **Pass if** | The backup returns the exact new code and calls the `read` tool; for the PDF, the code and page 2, with the PDF delivered to the backup natively |
| **Checked in** | The export, including input token counts |
| **Result** | Cheap: pass. Best: **partial**. Image and tools passed. The PDF answer was correct, but the first request to the backup carried almost no PDF tokens and the model used a subagent to get the answer, so native delivery after a failover is not confirmed |

### Test 8: Memory across sessions

| | |
|---|---|
| **Checks** | Project facts reach a fresh session, and a resumed session keeps its own context |
| **Why** | These are the two kinds of memory this guide relies on, in place of a memory plugin |
| **Setup** | The test repository, whose `AGENTS.md` contains a made-up codename that appears nowhere else |
| **Scenario** | Fresh session: "What is this project's codename? Answer from what you already know, without using tools." Resume: in another session send "Our objective for this session is to rename add to sum, and the next action is updating the test. Do not do it yet. Just confirm in one sentence.", leave it, reopen it from the sidebar, and ask "What was our objective and the next action? Answer in one sentence." |
| **Pass if** | The codename comes back with **no tool calls**, so it came from `AGENTS.md` and not from reading files; the resumed session states both the objective and the next action, and no new session was created |
| **Checked in** | The export, including the tool list |
| **Result** | Best: pass. Cheap (GLM): pass |

### Test 9: Semantic memory

Out of scope, for the reasons in `protocol-results.md`. It is listed so the numbering matches the evidence files.

### Test 10: Compaction

| | |
|---|---|
| **Checks** | After the context is compacted, the task survives |
| **Why** | Compaction is lossy by design. The question is whether it keeps what matters |
| **Setup** | A session with an objective, a decision and a next action stated up front, followed by turns that read files |
| **Scenario** | "Our objective: add a multiply function to src/math.mjs. Decision: keep it dependency free, per docs/DECISIONS.md. Next action: write the test first. Do not edit anything. Confirm in one sentence." Then two file-reading prompts, then `/compact`, then "State the objective, the decision, and the next action. Do not use tools." |
| **Pass if** | The export shows that compaction ran, and the answer after it names all three: multiply, no dependencies, and test first |
| **Checked in** | The export, before and after compaction |
| **Result** | Best: pass. Cheap: pass |

### Test 11: Subagent bounds

| | |
|---|---|
| **Checks** | The orchestrator respects limits on how many subagents it starts and what they may do |
| **Why** | Unbounded subagents multiply cost, and nested ones are hard to follow |
| **Setup** | The test repository |
| **Scenario** | "Use at most two subagents in parallel: one to summarise src/math.mjs and one to summarise test/math.test.mjs. Neither may edit, and neither may launch further agents. Then combine the two summaries in two sentences." |
| **Pass if** | Exactly two subagents, no edit tools, no nested subagents, and a combined answer |
| **Checked in** | The tool calls in the export |
| **Result** | Best: pass. Cheap (GLM with the rule): pass. One run each |

### Test 12: Permissions

| | |
|---|---|
| **Checks** | The permission rules in the article's configuration section allow, deny and ask as written |
| **Why** | These rules are what stands between the agent and a destructive command |
| **Setup** | The test repository, with the untracked `.env` and no remote |
| **Scenario** | Five prompts, each asking the agent to run one command exactly: `git status --short`, `git push --dry-run origin main`, `rm -rf build`, a read of `.env`, and `ls src`. Every prompt that appeared was answered **Deny** |
| **Pass if** | `git status` runs with no prompt; `git push` and `rm -rf` are refused with no prompt; the `.env` read and `ls` ask first; `HEAD` does not move |
| **Checked in** | Tool states in the export, and `git rev-parse HEAD` before and after |
| **Result** | Best: pass. Not repeated on Cheap: OpenCode applies these rules before a command runs, whichever model asked |

### Test 13: Rewind and Redo

| | |
|---|---|
| **Checks** | A bad turn can be undone and redone |
| **Why** | Recovery is what makes it safe to let an agent edit |
| **Setup** | The test repository with earlier edits committed, so only the new change is in play |
| **Scenario** | "Create the file scratch.txt containing exactly the word alpha. Nothing else." Then **Rewind to here** on that message, then **Redo** from the command palette |
| **Pass if** | After rewind the file is gone and the prompt is back in the composer; after redo the file is back |
| **Checked in** | The file on disk and `git status` after each step |
| **Result** | Best: pass. Not repeated on Cheap: snapshots do not involve the model |

### Test 14: Cost

| | |
|---|---|
| **Checks** | What the harness reports matches what providers bill, and what switching routes costs |
| **Why** | Failover changes where tokens go, and a route switch can lose the prompt cache |
| **Setup** | One session on Haiku |
| **Scenario** | Five one-word turns: two on Anthropic, two after switching to OpenRouter, one after switching back. "Reply with exactly one word: one", then "two", and so on |
| **Pass if** | Per-turn cost and cache tokens are recorded for each turn, and OpenCode's totals match the provider dashboards |
| **Checked in** | The export, then the dashboards |
| **Result** | Route-switch cost measured (see `protocol-results.md`). **Dashboard comparison not finished** |

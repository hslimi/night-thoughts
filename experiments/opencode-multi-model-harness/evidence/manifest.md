# Evidence manifest

Sanitizing replaces only absolute paths and keys. Statuses and results are not edited.

| File | Covers | Date | OpenCode |
|---|---|---|---|
| `static-capability-check.txt` | Static catalog check of Best and Cheap chains | 2026-11-05 | Not applicable |
| `desktop-pings-2026-11-05.md` | Desktop pings on Best and Cheap routes | 2026-11-05 | 2.2.5 |
| `glm-free-limit-failover.session.json` | Free-limit error followed by failover to a paid route | 2026-11-05 | 2.2.5 |
| `protocol-results.md` | Results per protocol test | 2026-11-05 | 2.2.5 |
| `best/01-tiers.session.json`, `best/01-tiers-router.session.json` | Test 1 | 2026-11-05 | 2.2.5 |
| `best/02-image.session.json` | Test 2 | 2026-11-05 | 2.2.5 |
| `best/03-pdf-native.session.json` | Test 3 | 2026-11-05 | 2.2.5 |
| `best/04-routing.session.json`, `best/04b-exploration-clone.session.json` | Test 4 | 2026-11-05 | 2.2.5 |
| `best/05-429-after-tool.session.json`, `best/05b-503.session.json` | Test 5 | 2026-11-05 | 2.2.5 |
| `best/06-no-first-token.session.json` | Test 6 | 2026-11-05 | 2.2.5 |
| `best/07-*.session.json` | Test 7 | 2026-11-05 | 2.2.5 |
| `best/08-*.session.json` | Test 8 | 2026-11-05 | 2.2.5 |
| `best/10-compaction.session.json` | Test 10 | 2026-11-05 | 2.2.5 |
| `best/11-swarm.session.json` | Test 11 | 2026-11-05 | 2.2.5 |
| `best/12-permissions.session.json` | Test 12 | 2026-11-05 | 2.2.5 |
| `best/13-*.session.json` | Test 13 | 2026-11-05 | 2.2.5 |
| `best/14-route-switch-cost.session.json` | Test 14 | 2026-11-05 | 2.2.5 |
| `cheap/*.session.json` | Cheap tests 1 to 4, 7, 10 | 2026-11-05 | 2.2.5 |
| `mock-provider.log` | Requests the mock provider received | 2026-11-05 | Not applicable |

## Screenshots

Captured from the OpenCode Desktop window only, on a clean profile in dark mode at 1440×900. Each was inspected before being kept. None has been uploaded.

| File | Alt text | Date |
|---|---|---|
| `screenshots/best-tiers-preset-and-models.png` | `/tiers` output in OpenCode Desktop showing the best-frontier preset, with Haiku on fast, Sonnet on medium, and Opus on heavy | 2026-11-06 |
| `screenshots/best-image-attachment-answer.png` | An attached image containing a code, and Claude Haiku 5.5 replying with that exact code | 2026-11-06 |
| `screenshots/best-failover-after-rate-limit.png` | A session where a test provider returns a rate limit error, OpenCode switches to Claude Haiku 5.5, and the backup continues the same task | 2026-11-06 |
| `screenshots/best-permission-prompt-for-env-file.png` | A Permission required prompt for reading a .env file, with Deny, Allow always, and Allow once buttons | 2026-11-06 |
| `screenshots/cheap-glm-delegates-edit-to-subagent.png` | A GLM-5.3-Flash session where a Medium subagent has finished an edit, and all 9 tests pass | 2026-11-06 |

# Documentation Link Audit

## Result

The audit covered the experiment README, article source, setup and reproduction instructions, generated public Markdown documents, relative links and anchors, local images, GitHub files/directories, external HTTP destinations, Hashnode CDN images, and the actual unpublished Hashnode draft body.

- Initial scan: 48 document sources, 207 link occurrences, 57 unique remote URLs, 81 raw findings.
- Three raw findings were reserved `example.*` or `github.com/example/*` illustrations, not real destinations; the checker now classifies them as illustrative examples.
- Actual repaired links: 78 occurrences.
- Final scan: zero broken links. Every Hashnode CDN image passed, every local image existed, and the checked local heading anchor resolved.

The complete initial findings are in [link-audit-before.json](./link-audit-before.json). The final machine-readable result is [link-audit-final.json](./link-audit-final.json).

## External replacements

| Document | Broken destination | Verified replacement |
|---|---|---|
| `article/article.md` and the Hashnode draft | `https://github.com/github/spec-kit/blob/main/docs/reference/agent-integrations.md` (404) | `https://github.com/github/spec-kit/blob/main/docs/integrations/copilot.md` |
| `.specify/extensions/bug/README.md` | `../EXTENSION-API-REFERENCE.md#hook-events` (missing file) | `https://github.com/github/spec-kit/blob/main/docs/extensions/api.md#hook-events` |

The Copilot replacement is the current official integration guide. It documents `specify init my-project --integration copilot` and the `.github/skills/speckit-<command>/SKILL.md` layout, supporting the article’s initialization and skill-invocation claims.

The extension replacement is the current official Extension API Reference. Its **Hook Events** heading and bundled bug-event entries support the README’s shared-hook-contract claim. The destination and heading were inspected directly in `github/spec-kit` and on the published documentation site.

## Relative-link replacements

| Document | Broken links | Repair |
|---|---:|---|
| `evidence/workflow/analysis-original.md` | 60 | Prefixed project-root `specs/` and `.specify/` destinations with `../../`; removed `:line-number` suffixes from destinations while preserving labels such as `plan.md:25`; mapped the shortened `spec.md:<line>` destinations to `../../specs/001-expense-tracker/spec.md`. |
| `evidence/workflow/convergence-final.md` | 1 | Changed `specs/001-expense-tracker/tasks.md` to `../../specs/001-expense-tracker/tasks.md`. |
| `evidence/workflow/convergence-first.md` | 2 | Changed `src/App.tsx` to `../../src/App.tsx` and `specs/001-expense-tracker/tasks.md` to `../../specs/001-expense-tracker/tasks.md`. |
| `evidence/workflow/copilot-stage-log.md` | 12 | Prefixed `specs/` destinations with `../../`; changed the constitution destination to `../../.specify/memory/constitution.md`; removed the link to machine-local, uncommitted `.specify/feature.json` and labelled it as intentionally uncommitted text. |
| `article/article.md` and Hashnode draft | 2 | Replaced the dead Copilot integration URL in both bodies. |
| `.specify/extensions/bug/README.md` | 1 | Replaced the missing extension API target with the current official URL and verified anchor. |

Every exact initial occurrence and its status is retained in `link-audit-before.json`; the table groups repeated path patterns rather than hiding them.

## Verification commands

Repository documents and all remote targets:

```bash
python3 scripts/audit-links.py --output evidence/verification/link-audit.json
```

Include a freshly retrieved draft without publishing it:

```bash
hashnode -p 6a9439bd520526685ca0ce83 --json draft get 6ae62b9522949cf8d9ef1cb0 > /tmp/spec-kit-link-audit-draft.json
python3 scripts/audit-links.py \
  --draft /tmp/spec-kit-link-audit-draft.json \
  --output evidence/verification/link-audit-final.json
```

The checker exits nonzero when a real broken link remains. Reserved example URLs are identified explicitly rather than treated as network failures. Runtime localhost URLs are excluded from availability checks because they require a running application.

The final retrieved draft body matched the repaired article with CDN image substitutions. Its content SHA-256 is `f329e4897545ab7b314a07dc0d0d9905d8fa52b21abc74dee0322eae3aa751d3`. It remains unpublished, unscheduled, and not submitted for review.

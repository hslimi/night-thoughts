# Official Documentation Consulted

Consulted on 2026-10-31 before installation and implementation.

## GitHub Spec Kit 1.2.5

- Repository and current process overview: https://github.com/github/spec-kit
- SDD quickstart: https://raw.githubusercontent.com/github/spec-kit/v1.2.5/docs/quickstart.md
- Kimi Code integration: https://raw.githubusercontent.com/github/spec-kit/v1.2.5/docs/integrations/kimi.md
- Bug-fixing quickstart: https://raw.githubusercontent.com/github/spec-kit/v1.2.5/docs/guides/bugfix.md
- Documentation home: https://github.github.com/spec-kit/

The installed CLI help confirmed `specify init ... --integration kimi --script sh --non-interactive` and `specify extension add bug`. Kimi skills are installed under `.kimi-code/skills/` and invoked as `/skill:speckit-*` through `kimi -p`.

## Hashnode CLI 0.1.1

- Official package and command documentation: https://www.npmjs.com/package/@hashnode/cli
- Installed help checked with `hashnode --help`, `hashnode draft create --help`, `hashnode draft list --help`, and `hashnode image upload --help`.
- Authentication checked with `hashnode whoami`; publication access checked with `hashnode publication list` and `hashnode --host nightthoughts.me publication get`.
- The requested `nighthoughts.me` hostname returned NOT_FOUND. The authenticated publication is `nightthoughts.me`, ID `6a9439bd520526685ca0ce83`.
- Existing drafts were listed before article creation; no matching title was present.
- Valid tags checked with the CLI: `github`, `ai`, `typescript`, `software-development`, and `tutorials`.

# Separate Copilot Read-Only Demonstration

This workspace exists to demonstrate GitHub Copilot Chat with Spec Kit without relabelling the Kimi-generated application workflow.

It was initialized with Spec Kit 1.2.5:

```sh
specify init copilot-demo --integration copilot --script sh --non-interactive
```

The official integration installs `.github/skills/speckit-*/SKILL.md`. The completed read-only demonstration used:

```text
/speckit-analyze
```

The frozen specification, plan, task list, verification, and constitution were copied here before the chat run. The generated application and its Kimi execution artifacts stay under `../app/` and `../evidence/`; they are not represented as Copilot-generated. The first prompt failed because the active feature was unset. After adding `.specify/feature.json`, the rerun produced a genuine report with no critical issues or constitution conflicts and mapped coverage, while retaining open verification work. See `ANALYSIS-ATTEMPTS.md` for the exact outcome and `../assets/screenshots/16-copilot-read-only-analysis.png` for the genuine chat/artifact capture.

## Authentication status

Copilot initially required GitHub sign-in in both an isolated profile and the clean named profile. The user completed the normal GitHub sign-in flow, and the named `spec-kit-copilot` profile then showed Copilot as available. The successful read-only report is recorded in `ANALYSIS-ATTEMPTS.md`. Credentials are not stored in this workspace.

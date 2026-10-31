# Copilot Analysis Attempts

## Attempt 1: missing active feature

The genuine `/speckit-analyze` prompt was entered in GitHub Copilot Chat in the clean `copilot-demo` VS Code workspace. Copilot inspected the workspace but could not run analysis because `.specify/feature.json` did not exist and no `SPECIFY_FEATURE_DIRECTORY` was configured. It reported that no active feature directory could be resolved and that no files were modified.

The frozen artifact set was not changed by Copilot. I added `.specify/feature.json` containing `{"feature_directory":"specs/001-expense-tracker"}` to point the separate workspace at its existing snapshot, then reran the prerequisite check before the next prompt.

## Attempt 2: genuine read-only report

The prerequisite check resolved `specs/001-expense-tracker` successfully. I entered `/speckit-analyze` again in the same Copilot Chat and waited for the actual result. Copilot loaded the `speckit-analyze` skill, inspected the frozen artifacts, and produced a Specification Analysis Report.

Observed in the chat response:

- No critical issues or constitution conflicts were reported.
- All 29 functional requirements and SC-002–SC-010 had mapped coverage.
- Some mapped verification work remained open.
- The read-only analysis did not change the frozen artifacts.

The final VS Code capture shows this prompt and response beside `spec.md`. It is saved as `../assets/screenshots/16-copilot-read-only-analysis.png`. This is a separate Copilot analysis of a frozen artifact set, not a Copilot-generated application or implementation workflow.

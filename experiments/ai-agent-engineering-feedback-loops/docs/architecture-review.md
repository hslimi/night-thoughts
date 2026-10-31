# Architecture review

## Method and scope

I manually applied the deep-module survey from `improve-codebase-architecture` and `codebase-design` at upstream commit `a496f5513d4a4cf889bc48e189e579f4b0bdf6aa`; no upstream slash command ran. The captured survey was executed in GitHub Copilot Chat Ask mode and did not modify files.

The review covered `src/trial-ending-reminders.ts`, its public-seam tests, `GLOSSARY.md`, and ADR 0001. There is no route, SQL query, email handler, queue, or retry worker in this deliberately small example.

## Existing module shape

The public `sendTrialEndingReminder` seam owns status, future-time, 72-hour-window, existing-record, send, record, and retry behavior. Callers supply only the subscription, current instant, and two adapters. Tests cross the same seam as callers.

The policy passes the deletion test at this scale: removing the module would move all of those decisions back into callers. Extracting a separate eligibility function or adding pass-through modules would not improve locality or leverage.

## Selected candidate: domain-specific store vocabulary

- Recommendation strength: **Low**; an interface-vocabulary improvement, not an architectural defect.
- Problem: `ReminderStore` was generic in a module and glossary concerned specifically with trial-ending reminders.
- Change: rename the interface to `TrialEndingReminderStore` in the source and test adapter.
- Benefit: the adapter's role is clearer at the public seam without moving policy, adding infrastructure, or changing behavior.

The rename was applied after the GREEN run. No broader refactor was warranted. Atomic claims, concurrent workers, durable storage, and delivery-failure recovery remain explicit ADR non-goals rather than candidates to sneak into this example.

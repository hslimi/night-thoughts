# ADR 0001: Keep the trial-ending reminder policy in one deep module

- Status: Accepted
- Date: 2026-10-31

## Context

The vague request “email customers three days before their trial ends” leaves status, time boundaries, duplicate delivery, and infrastructure scope unresolved. Spreading those decisions across routes, queries, email handlers, and retry code would make the rule difficult to verify and change.

## Decision

Use one public `sendTrialEndingReminder` seam. The module owns all eligibility rules and the check–send–record sequence. Callers supply the current instant plus reminder-store and email adapters.

Use UTC instants and a 72-hour elapsed-time window. Only future-ending, trialing subscriptions without a recorded trial-ending reminder are eligible. Record after a successful send so a worker retry skips delivery.

Test behavior through the public seam with in-memory adapters. Keep real delivery, persistence, queues, HTTP, billing, concurrent-worker claims, and failure recovery out of this example.

## Consequences

The complete policy is locally readable and executable through tests. A production implementation must provide durable adapters and revisit atomic claiming, concurrent workers, and failures between email delivery and recording; this experiment does not claim to solve those problems.

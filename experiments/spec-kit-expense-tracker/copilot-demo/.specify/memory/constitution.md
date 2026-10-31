<!--
Sync Impact Report
- Version change: none → 1.0.0 (initial ratification)
- Modified principles: none; all six principles are newly established
- Added sections: Core Principles; Additional Constraints; Quality Gates; Governance
- Removed sections: none
- Follow-up TODOs: none
-->

# Personal Expense Tracker Constitution

## Core Principles

### I. Exact Money Representation

All monetary amounts MUST be represented and persisted as integer minor units, such as cents.
Calculations MUST use exact integer arithmetic; binary floating-point values MUST NOT represent
or calculate money. Input parsing, validation, and output formatting MUST convert explicitly
between user-facing values and minor units. Every displayed amount MUST include explicit,
currency-aware formatting. This prevents rounding drift and ambiguous currency presentation.

### II. Accessible by Design

The application MUST target WCAG 2.2 Level AA. Interactive elements MUST use semantic controls;
forms and dialogs MUST be fully operable by keyboard with appropriate labels and instructions.
Dialogs MUST manage focus on entry, contain it while modal, and restore it on close. Focus MUST
remain visible, and text, controls, and meaningful states MUST meet accessible contrast
requirements. Accessibility is a completion requirement, not a later refinement.

### III. Meaningful Behavioral Testing

Business-logic tests MUST cover amount validation, calendar month boundaries, totals, filtering,
sorting, persistence, and malformed stored data, including boundary and failure cases. Important
UI interactions MUST also be tested through observable user behavior, including keyboard use,
confirmation flows, and persistence-error presentation. Tests MUST be capable of failing when
the required behavior regresses; implementation-only or trivial assertions do not satisfy this
principle.

### IV. Separated, Typed Modules

React components MUST remain responsible for rendering and interaction, pure modules MUST own
calculations and business rules, and a separate persistence module MUST own all localStorage
access. These concerns MUST NOT be intermingled. Modules MUST remain small, have explicit typed
interfaces, and expose dependencies through clear boundaries so calculations can be tested
without React or browser storage.

### V. Explicit Destructive Confirmation

Every action that deletes, clears, or irreversibly replaces user data MUST require explicit
confirmation immediately before execution. The confirmation MUST identify the affected data and
consequence, provide a safe cancellation path, and perform no destructive work until the user
affirmatively confirms. Ambiguous gestures, preselected destructive choices, and bulk actions
without confirmation are prohibited.

### VI. Transparent, Non-Destructive Persistence Recovery

localStorage read and write failures MUST produce a visible, understandable user-facing status;
failures MUST NOT be swallowed or reported only to a developer console. Missing data MUST be
handled as a defined empty or initial state. Malformed or unreadable data MUST be detected and
reported, with valid in-memory work retained where possible. Recovery MUST NOT silently discard,
reset, or overwrite existing data; replacing or clearing unrecoverable data requires informed
user confirmation.

## Additional Constraints

The product MUST remain a frontend-only personal expense tracker. Runtime behavior MUST NOT
require an application server or remote database, and localStorage is the sole durable
persistence boundary. Currency, date, validation, and storage rules MUST apply consistently
across UI interactions and tests.

## Quality Gates

Reviews MUST examine generated artifacts—including specifications, plans, tasks, implementation,
and tests—for consistency with the constitution and the requested behavior. Behavioral tests
MUST exercise meaningful outcomes and failure paths rather than merely satisfy coverage metrics.
Review and testing MUST converge before completion: identified defects and governance violations
MUST be resolved or explicitly accepted by the user, relevant checks MUST be rerun, and no known
failing required check or unresolved critical review finding may remain.

## Governance

This constitution supersedes conflicting project practices. Amendments require a documented
rationale, review of affected artifacts, and an updated semantic version and amendment date.
MAJOR increments denote backward-incompatible principle removals or redefinitions; MINOR
increments denote new or materially expanded principles or sections; PATCH increments denote
non-semantic clarifications. Every implementation review MUST verify compliance with all six
principles, review generated artifacts, require meaningful behavioral tests, and enforce the
quality gates. Work is complete only after review and test results converge, all required checks
pass, and any accepted exceptions are explicitly recorded.

**Version**: 1.0.0 | **Ratified**: 2026-10-31 | **Last Amended**: 2026-10-31

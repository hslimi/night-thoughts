<!--
Sync Impact Report
Version change: unknown (unfilled scaffold) -> 1.0.0
Modified principles: none (prior document contained placeholders only)
Added principles: I. Exact Monetary Arithmetic; II. Accessible Keyboard-First Interactions;
III. Business-Logic Testing; IV. Separation of Concerns; V. Confirmed Destructive Actions;
VI. Visible Persistence Outcomes
Added sections: Technical Constraints; Proportionate Delivery
Removed sections: none
Follow-up TODOs: none.
-->
# Expense Tracker Constitution

## Core Principles

### I. Exact Monetary Arithmetic
All monetary values used in calculations and persistence MUST be represented as integer cents.
Parsing and conversion MUST preserve cents exactly and reject unsupported precision rather than
introducing floating-point errors. Formatting for display MUST happen at the presentation boundary.

### II. Accessible Keyboard-First Interactions
Forms and dialogs MUST be operable by keyboard, use semantic controls with accessible names, and
make validation feedback available to assistive technology. Dialogs MUST manage focus when opened
and closed so users can complete or cancel tasks without a pointer.

### III. Meaningful Business-Logic Testing
Tests MUST cover monetary calculations and other business rules, including relevant validation and
boundary cases. Tests MUST verify observable outcomes rather than merely mirror implementation
details; UI-only checks do not replace business-logic tests.

### IV. Separation of Concerns
The UI, business calculations, and persistence MUST have clear, maintainable boundaries. Monetary
rules MUST not be embedded in rendering code, and persistence details MUST not be duplicated
throughout the UI. Keep the boundaries simple and proportionate to this application.

### V. Confirmed Destructive Actions
Actions that delete or irreversibly clear expense data MUST require explicit confirmation before
they take effect. Users MUST be able to cancel without changing their data.

### VI. Visible Persistence Outcomes
Persistence failures MUST be communicated visibly and accessibly; they MUST NOT be silently
ignored or presented as successful saves. The UI MUST keep the user informed when data could not
be saved so the failure can be addressed.

## Technical Constraints

This is a frontend-only expense-tracker demonstration built with React, TypeScript, and Vite.
Implementation MUST keep expense data handling in the frontend and MUST preserve type safety
across UI, calculation, and persistence boundaries.

## Proportionate Delivery

Specifications, plans, and task lists MUST be limited to the work needed for this small application.
They MUST stay concise and actionable; avoid oversized plans, unnecessary abstractions, and
unrequested infrastructure.

## Governance

The constitution governs feature specifications, plans, tasks, implementation, and review.
Amendments MUST document their rationale, preserve applicable principles, and update this document's
version and amendment date. The project maintainer reviews amendments and resolves conflicts between
proposed work and these principles before implementation proceeds.

Versioning follows semantic versioning: increment MAJOR for backward-incompatible governance
changes or principle removals/redefinitions, MINOR for new principles or materially expanded
requirements, and PATCH for clarifications and non-semantic wording changes. The last-amended date
MUST be updated for every amendment.

Every feature plan, task list, and code review MUST check applicable principles. Any necessary
deviation MUST be explicitly justified and approved by the project maintainer. Reviews MUST verify
that monetary rules are tested, accessibility requirements are addressed, destructive actions are
confirmed, and persistence failures are visible.

**Version**: 1.0.0 | **Ratified**: 2026-11-03 | **Last Amended**: 2026-11-03

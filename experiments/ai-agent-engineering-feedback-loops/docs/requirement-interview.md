# Requirement interview

## Interview method

I manually applied the interview structure from `grill-me`, `grilling`, and `grill-with-docs` at upstream commit `a496f5513d4a4cf889bc48e189e579f4b0bdf6aa`. No upstream slash command ran. The captured requirement-interview prompts were executed in GitHub Copilot Chat.

The experiment brief already supplied the decisions below. I organized them into decision rounds; I did not invent another user interaction.

## Intentionally vague initial request

> A TypeScript subscription service must email customers three days before their trial ends.

## Round 1: eligibility and time

### Q1 — Which subscriptions are eligible?

Should every subscription with a `trialEndsAt` date receive the email, or only subscriptions whose status is `trialing`?

**Confirmed answer:** Only `trialing` subscriptions are eligible. Cancelled subscriptions receive no reminder.

### Q2 — What does “three days before” mean?

Is this a calendar-day rule in a customer's local timezone, or an elapsed-time rule evaluated by a worker?

**Confirmed answer:** Use UTC and an elapsed-time window. Send when `trialEndsAt` is in the future and at most 72 hours away. Exactly 72 hours is eligible; more than 72 hours is not.

### Q3 — What happens after the trial ends?

Should an overdue trial receive a late reminder if a worker finds it?

**Confirmed answer:** No. Expired trials receive no reminder, and a trial ending exactly at the current instant is no longer in the future.

## Round 2: delivery and retries

### Q4 — How is a duplicate prevented?

Can the worker rely on the email provider, or must the application retain delivery knowledge?

**Confirmed answer:** The application checks for a recorded trial-ending reminder before sending and records one after sending. A retry of the same subscription must not send another reminder.

### Q5 — How much infrastructure belongs in this example?

Should the exercise include a real email provider, persistent database, queue, HTTP API, or billing integration?

**Confirmed answer:** No. Use small adapters in tests. Real email, distributed queues, HTTP, billing, concurrent-worker claims, and failure recovery are outside the experiment.

## Agreed public test seam

Tests call `sendTrialEndingReminder` with a subscription, the current UTC instant, a reminder store, and an email adapter. They observe the returned result, recorded reminders, and emails sent through that same seam.

This seam catches eligibility, boundary, and retry errors. It does not test a real database, SMTP provider, queue, or concurrent workers.

## Result

The decisions are recorded in [the behavior contract](behavior-contract.md), [GLOSSARY.md](../GLOSSARY.md), and [ADR 0001](adr/0001-trial-ending-reminder-policy.md) before implementation.

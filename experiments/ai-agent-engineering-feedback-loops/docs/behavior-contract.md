# Behavior contract

Send one **trial-ending reminder** for a subscription only when all of these conditions hold:

1. The subscription status is `trialing`.
2. `trialEndsAt` is strictly after the current instant.
3. `trialEndsAt` is at most 72 hours after the current instant.
4. No trial-ending reminder is already recorded for the subscription.

When the module sends an email, it records the trial-ending reminder. Calling the same worker operation again for that subscription skips delivery.

## Boundaries

- Exactly 72 hours away: send.
- 72 hours plus one millisecond away: skip.
- Exactly the current instant: skip.
- In the past: skip.
- Cancelled or otherwise non-trialing: skip.
- Already recorded: skip.
- Second call after a successful first call: skip.

All comparisons use absolute instants, expressed and documented as UTC. No local calendar arithmetic is involved.

## Deliberate non-goals

This experiment does not implement a real email integration, persistent storage, a distributed queue, an HTTP API, billing, concurrent-worker coordination, or delivery-failure recovery.

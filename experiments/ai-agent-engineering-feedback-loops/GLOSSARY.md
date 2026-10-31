# Glossary

## Subscription

A customer's subscription, identified by `id`, with an email address, a status, and a trial-ending instant.

## Trialing

The only subscription status eligible for a trial-ending reminder. `active` and `cancelled` subscriptions are not eligible.

## Trial-ending reminder

The single email reminding a customer that their trial is approaching its end.

## Eligibility window

The interval beginning strictly after the current instant and ending exactly 72 hours after it. `trialEndsAt` must fall inside this interval.

## Trial-ending reminder record

Application-side knowledge that a trial-ending reminder has been sent for a subscription. Its presence prevents another send.

## Worker retry

A repeated invocation for the same subscription after a successful send. It must produce no duplicate email.

## UTC instant

An absolute point in time, represented by JavaScript `Date` and compared by epoch milliseconds. The module does not perform local calendar arithmetic.

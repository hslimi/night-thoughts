# Reviewer Decisions After the Quality Checklist

The custom checklist initially contained 37 unchecked findings. These are the reviewer-supplied decisions used in the remediation pass. They are product and verification decisions, not claims that implementation is complete.

## Accessibility

- Enumerate month selection, filtering, sorting, empty-state actions, persistence recovery, demo interactions, and CRUD as core flows.
- Require zero known WCAG 2.2 AA violations at completion rather than accepting unspecified non-critical accessibility defects.
- Focus the first invalid field. Associate and announce errors and status messages; never rely on color alone.
- Give replacement dialogs the same focus rules as deletion dialogs.
- Verify 200% zoom, 320 CSS-pixel reflow, and 24 CSS-pixel minimum targets.

## Money

- Trim surrounding whitespace.
- Accept digits with one or two optional decimal places, leading zeros, and `.50`.
- Reject trailing decimal points, grouping separators, currency symbols, explicit plus signs, exponent notation, and amounts above `999999999.99` USD.
- Persist integer cents. Reject unsafe aggregate totals visibly rather than rounding.
- Use locale-independent USD formatting with `$0.00` and `$1,234.56` examples.
- Sort equal amounts or dates by ascending ID in both directions.

## Persistence

- Validate a stored collection as all-or-nothing.
- Unreadable storage cannot have its raw value inspected. Preserve it by performing no write until explicit confirmation.
- Failed add, edit, and delete changes remain visible only in memory. Reload restores the last durable collection. A later successful save persists all current work and clears the warning.
- Concurrent normal-tab synchronization is excluded. Quota exhaustion, serialization failures, and mid-session storage failures are visible write failures.

## Demo and verification

- Demo activation uses the first `demo` query value exactly and case-sensitively. Unrelated query parameters are allowed.
- Mode transitions use navigation or reload with fresh state. Add is supported in demo mode.
- Demo mode must not read or write real storage or register storage-event listeners. Verification must instrument all three prohibitions.
- Use the fixed ten-record demo baseline and independently checked October totals in `demo-arithmetic.txt`.
- Define reproducible verification cases and a deterministic 1,000-record fixture. “Immediate” means visible within two seconds in reference Chromium.
- Chromium is the acceptance browser. Other browsers remain unverified.

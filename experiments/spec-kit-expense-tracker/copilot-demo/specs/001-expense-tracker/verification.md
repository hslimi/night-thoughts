# Verification: Personal Expense Tracker

Verified on 2026-11-01 against the production build and reference Chrome for Testing 156.0.8078.4 (Playwright Chromium v1248). React 19.3.1, TypeScript 5.9.3, Vite 8.3.5, Vitest 4.1.12, and Playwright 1.64.1 were used.

Every `Chromium` evidence citation below refers to that exact reference browser version. `Unit` means Vitest domain/persistence tests; `UI` means React Testing Library in jsdom. `Manual T048` refers to the completed persistence/recovery review; it is not a claim of screen-reader testing. No operating-system assistive technology was enabled during the T053/T055/T056 convergence work.

## Automated and production results

| Check | Actual result |
| --- | --- |
| `npm run test:unit` | 18 files and 260 tests passed |
| `npm run build` | TypeScript check and Vite production build passed |
| `npm run test:e2e` | 167 passed; 1 intentionally skipped mobile duplicate of the desktop browser-zoom scenario |
| Automated WCAG 2.2 AA scans with `@axe-core/playwright` | Zero reported violations in the covered states |
| SCALE-001/002 | 1,000 records restored exactly; 45 timed interactions per layout, each within 2 seconds |
| Independent production browser scenario | 12 checks passed; no console errors |
| Convergence month-input regression (T051) | The behavioral test reproduced the crash before the fix and passes after it. Clearing Month preserves the prior valid month and dashboard with no page errors. |
| CORE-006 amount-resorting regression (T053) | Before correction, the unchanged desktop scenario failed 2 of 30 repetitions because the original 100-cent amount was submitted after `4.00` had been filled. After correction, the same unchanged scenario passed 100 of 100 desktop repetitions and its affected UI suite passed 10 of 10 tests. |
| Desktop/mobile layout checks | No horizontal overflow at 1440px or 390px; separate 320px reflow, zoom, text-resize, and target checks passed |

The final ordered sequence was run after the T053 correction: `npm run test:unit`, then `npm run build`, then `npm run test:e2e`; all completed with the results above.

The production scenario exercised create, exact monthly/category totals, adjacent-month exclusion, category filtering, amount sorting, editing, deletion Cancel/Escape/confirmation, reload persistence, invalid amounts, keyboard submission, month navigation, malformed-storage preservation, and responsive overflow. Its output is `evidence/production-browser.txt` in the experiment folder.

## CORE-006 investigation and correction

- **Repeated evidence:** the unmodified desktop `CORE-006: visible same-month edit restores the requester after amount resorting` scenario failed 2 of 30 runs. Both failures expected `newer` at amount-ascending index 1 but found `tie-c` still at its original 100-cent position for the full assertion timeout. The trace showed that `4.00` had been filled before Save changes was activated.
- **Demonstrated cause:** edit draft initialization ran in a passive `useEffect`. The edit heading could become visible before that effect finished; a fast amount input could then be overwritten by the original expense draft and submitted successfully, leaving the amount order unchanged. The comparator was not the source of the failure.
- **Targeted correction:** `src/components/ExpenseForm.tsx` now initializes the edit draft in `useLayoutEffect`, so the draft and initial focus are settled before the browser paints and accepts subsequent input. No sorting, persistence, or focus-request logic was changed.
- **Assertion integrity:** `e2e/transaction-list.spec.ts` was not changed. Exact amount-resorted IDs and requester focus remain asserted. The corrected scenario passed 100 consecutive desktop repetitions; the complete Chromium run also passed on desktop and mobile.

## Manual review record

| Review | Result |
| --- | --- |
| Keyboard and native-dialog behavior | Pass. Production submission worked by keyboard. Delete opened a native dialog with Cancel focused; Escape preserved the record. Chromium tests also cover Tab/Shift+Tab containment, restoration, filtered edits, and all deletion fallbacks. |
| Responsive visual review | Pass. Actual 1440×900 and 390×844 production viewports were inspected after capture. The summary, controls, transactions, and dialog are legible; fictional data is identified in the application. |
| PERSIST and RECOVERY review | Pass for PERSIST-001–013 and RECOVERY-001–007. Case-level preconditions, inputs, actual outcomes, raw-data/no-write claims, retained work, warning lifecycle, and reload results are recorded below. |
| VoiceOver with Chromium | **Not completed.** A historical validation attempt obtained no reliable audible or caption evidence. No screen-reader verification is claimed, and no assistive technology was enabled during this convergence work. |

The VoiceOver limitation leaves T047 open. T050 cannot claim the complete accessibility gate described by the original task. Automated scans and keyboard/manual browser checks are not represented as substitutes for screen-reader review.

## PERSIST and RECOVERY case-by-case review

All rows below passed the manual T048 evidence review and the cited automated checks. Readable cases compared the exact raw string; unreadable cases made no raw-value inspection claim and asserted write counts instead.

| Case | Precondition | Input/action | Actual outcome | Evidence |
| --- | --- | --- | --- | --- |
| PERSIST-001 | Storage key is absent. | Open normal tracker at fixed local 2026-10-31. | Ready empty October dashboard, `$0.00`, no recovery/start-fresh UI, zero writes. | Manual T048; unit `expenseStorage.load.test.ts`; UI `persistenceStatus.test.tsx`; Chromium `persistence.spec.ts`. |
| PERSIST-002 | Valid version-1 envelope contains three distinct records, including a previous-month maximum amount and exact notes. | Open, inspect October and September, reload. | Complete collection restored once with exact IDs, values, notes, month membership, and totals; raw value unchanged; zero writes. | Manual T048; unit load/write tests; UI `recovery.test.tsx`; Chromium `persistence.spec.ts`. |
| PERSIST-003 | Readable malformed JSON, including non-ASCII and whitespace bytes. | Open and cancel start-fresh recovery. | Empty guarded memory and announced warning; no salvage or writes; exact raw string unchanged before and after cancellation. | Manual T048 plus production malformed-cancel review; unit load test; UI `recovery.test.tsx`; Chromium `persistence.spec.ts`. |
| PERSIST-004 | Readable envelope has unsupported version 2 or an invalid expenses shape. | Open each variant and cancel replacement. | Each whole collection rejected; guarded empty state/warning retained; exact raw value unchanged and zero writes. | Manual T048; unit parameterized load cases; Chromium parameterized `persistence.spec.ts`. |
| PERSIST-005 | Otherwise valid envelope contains one record with fractional cents; unit cases cover other invalid fields. | Open and cancel replacement. | Entire collection rejected, including the valid-looking record; empty guarded state; raw value unchanged and zero writes. | Manual T048; unit parameterized load cases; Chromium `persistence.spec.ts`. |
| PERSIST-006 | Envelope contains duplicate IDs with otherwise valid records. | Open and cancel replacement. | Entire collection rejected with recovery warning; no record loaded, raw value unchanged, zero writes. | Manual T048; unit load test; Chromium `persistence.spec.ts`. |
| PERSIST-007 | Storage `getItem` throws `SecurityError`. | Open and cancel replacement. | Empty guarded memory and unreadable warning; no raw-inspection message/claim; zero writes before and after cancellation. | Manual T048; unit load test; UI `recovery.test.tsx`; Chromium `persistence.spec.ts`. |
| PERSIST-008 | One durable record; quota failure injected for the next add write. | Add `$23.45` note `Quota-only memory`, then reload. | Added work and unsaved-add warning remain only in memory; one failed write; durable raw value unchanged; reload omits new record and restores durable record. | Manual T048; unit write test; UI `persistenceStatus.test.tsx`; Chromium `persistence.spec.ts`. |
| PERSIST-009 | Durable target is `$1,234.56` with original note; writes fail. | Edit to `$99.99` and `Failed edit memory only`, then reload. | Edited fields and unsaved-edit warning remain only in memory; raw value unchanged; reload restores original amount/note and clears warning. | Manual T048; Chromium `edit-delete.spec.ts`. |
| PERSIST-010 | Durable target exists; writes fail. | Confirm target deletion, then reload. | Target absent only in memory with unsaved-delete warning; raw value unchanged; reload restores target and clears warning. | Manual T048; Chromium `edit-delete.spec.ts` with DELETE-004. |
| PERSIST-011 | One durable record; envelope serialization throws. | Add `$10.01` note `Serialization-only memory`. | Work and write warning remain visible; no durability success, destructive fallback, or storage write; original raw value unchanged. | Manual T048; unit write test; UI `persistenceStatus.test.tsx`; Chromium `persistence.spec.ts`. |
| PERSIST-012 | One durable record; storage write access fails mid-session. | Add `$19.99` note `Access-failure memory`, then reload. | Complete add and warning remain only in memory; one failed write and unchanged raw value; reload restores only durable record. | Manual T048; unit write test; UI `persistenceStatus.test.tsx`; Chromium `persistence.spec.ts`. |
| PERSIST-013 | One durable record; first add write fails, later writes are restored. | Add retained `$2.25`, then later `$3.75`; inspect envelope and reload. | Warning remained until successful mutation; later save wrote all three records in one version-1 envelope, cleared warning, and reloaded exact retained work with `$18.50` total. | Manual T048; unit write test; UI `persistenceStatus.test.tsx`; Chromium `persistence.spec.ts`. |
| RECOVERY-001 | Readable malformed value and empty guarded memory. | Start fresh, then Cancel and separately Escape. | No write either time; exact raw value and empty memory unchanged; warning remains; dialog focus contained and restored to Start fresh. | Manual T048; UI `recovery.test.tsx`; Chromium `persistence.spec.ts`. |
| RECOVERY-002 | Readable `{broken` guarded state. | Confirm start fresh, then reload. | Exactly one write of `{version:1,expenses:[]}`; ready empty state and warning clearance survive reload. | Manual T048; UI `recovery.test.tsx`; Chromium `persistence.spec.ts`. |
| RECOVERY-003 | Readable malformed state; confirmed write fails with quota error. | Confirm start fresh and wait for possible retry. | Empty guarded memory and recovery/write warning remain; no success claim, raw value unchanged, exactly one attempted write and no automatic retry. | Manual T048; UI `recovery.test.tsx`; Chromium `persistence.spec.ts`. |
| RECOVERY-004 | Readable malformed state; guarded adds of `$4.25` and `$5.75`. | Attempt first save, then Cancel; repeat with Escape. | No writes; both work items remain visible in memory; exact raw value and recovery warning remain; requester focus restored. | Manual T048; UI `recovery.test.tsx`; Chromium `persistence.spec.ts`. |
| RECOVERY-005 | Readable malformed state; guarded `$7.10` and `$8.20` records, one prior cancellation. | Confirm first replacement, then reload. | One write replaces old value with complete two-record current collection; ready state and warning clearance survive reload; `$15.30` total restored. | Manual T048; UI `recovery.test.tsx`; Chromium `persistence.spec.ts`. |
| RECOVERY-006 | Readable malformed state with guarded `$11.11` work. | Confirm replacement under serialization, quota, and access failures separately. | Each variant retains work and recovery/write status without success or retry; raw value unchanged; serialization causes zero writes, quota/access one failed write. | Manual T048; UI quota/serialization cases; Chromium all three parameterized cases. |
| RECOVERY-007 | Unreadable storage; three guarded work items. | Cancel first save, fail second confirmation, then successfully confirm third; inspect final envelope. | No pre-confirmation writes and no raw-inspection claim; cancelled/failed work retained; one failed confirmed write followed by one successful write of all three records; warning clears only after success. | Manual T048; UI `recovery.test.tsx`; Chromium `persistence.spec.ts`. |

## General case evidence inventory

This inventory supplies the precondition, input, actual outcome, and evidence for every non-PERSIST/RECOVERY case referenced by the requirement audit. The requirement matrix below maps each requirement to these detailed rows rather than duplicating them.

| Case | Precondition | Input/action | Actual outcome | Evidence |
| --- | --- | --- | --- | --- |
| AMOUNT-001 | Run in add and edit against an existing `$10.00` record. | `1`, `1.2`, `1.23`. | Accepted respectively as 100, 120, and 123 integer cents; exact USD values rendered and persisted. | Automated unit `money.test.ts`; UI add/edit parameterized tests; MONEY-004 storage round trips. |
| AMOUNT-002 | Same add/edit precondition. | `  001.2  `, `000.50`, `.50`. | Trimmed/accepted as 120, 50, and 50 integer cents. | Automated unit/UI parameterized tests; MONEY-004 storage round trips. |
| AMOUNT-003 | Same add/edit precondition. | `0.01`, `999999999.99`. | Accepted as 1 and 99999999999 cents; maximum renders `$999,999,999.99`. | Automated unit/UI parameterized tests; Chromium `core.spec.ts`; MONEY-004 storage round trips. |
| AMOUNT-004 | Same add/edit precondition; unchanged summaries/raw record expected. | Empty, whitespace, `0`, `0.00`, `000`, `-1`. | Every input rejected with associated amount error and focus; no mutation. Production also checked `-1` and `0`. | Automated unit/UI parameterized tests; production scenario. |
| AMOUNT-005 | Same add/edit precondition. | `.`, `1.`, `1.234`. | Every input rejected without rounding or mutation; amount error focused/associated. Production checked `1.234`. | Automated unit/UI parameterized tests; production scenario. |
| AMOUNT-006 | Same add/edit precondition. | `1,000`, `$1`, `+1`, `1e2`. | Every input rejected without mutation; amount error focused/associated. | Automated unit/UI parameterized tests. |
| AMOUNT-007 | Same add/edit precondition. | `abc`, `NaN`, `Infinity`. | Every input rejected without mutation; amount error focused/associated. Production checked `abc`. | Automated unit/UI parameterized tests; production scenario. |
| AMOUNT-008 | Same add/edit precondition. | `1000000000.00`, `1000000000`. | Both above-maximum inputs rejected without mutation; amount error focused/associated. | Automated unit/UI parameterized tests. |
| CORE-001 | Empty normal collection. | Add food `$25.50` on 2026-10-15. | One record; October monthly/food totals `$25.50`, other categories `$0.00`. | Automated unit `dashboard.test.ts`; Chromium `core.spec.ts`; production create scenario. |
| CORE-002 | Local current date fixed to 2026-10-31. | Open normal mode; separately clear native Month. | Initial month is 2026-10; clearing preserves the last valid month/dashboard without a crash. | Automated unit dates/UI tests; Chromium `core.spec.ts`; T051 desktop/mobile regression. |
| CORE-003 | Draft/persisted validation available. | Add each of food, transport, housing, entertainment, other; attempt invalid category. | Five valid categories work independently; invalid draft category is rejected and invalid persisted collection fails all-or-nothing validation. | Automated unit `expense.test.ts`; UI `addExpense.test.tsx`; Chromium `core.spec.ts`; PERSIST-005. |
| CORE-004 | Add and edit forms. | Blank, whitespace-only, and exact nonblank notes including surrounding whitespace/newline. | Blank notes omitted; nonblank notes preserved exactly on the same record. | Automated unit `expense.test.ts`; UI add/edit tests; Chromium `core.spec.ts` and `edit-delete.spec.ts`. |
| CORE-005 | Existing identified record and adjacent-month variants. | Edit all fields; move September→October and October→November; same-month amount resort in CORE-006. | Same ID and exact recalculation/durable values; selected month unchanged; visible requester focus for same-month edit, move announcement and Month focus for cross-month edits. | Automated UI `editExpense.test.tsx`; Chromium `edit-delete.spec.ts`. |
| CORE-006 | Category-filtered record and separate amount-ascending fixture. | Move matching record to another category without changing month; separately change `tie-c` from `$1.00` to `$4.00`. | Filtered record leaves results with announcement, unfiltered summaries, and Category-filter focus; visible amount edit orders `older,newer,tie-a,tie-b,tie-c` and restores its requester. | Automated UI `transactionPreferences.test.tsx`; Chromium `transaction-list.spec.ts`; 100/100 post-fix desktop repetitions. |
| DATE-001 | Records on 2026-09-30, 2026-10-01, 2026-10-31, 2026-11-01. | Select October. | Only October 1/31 records and amounts contribute. | Automated unit dashboard/dates tests; UI monthly dashboard; Chromium `core.spec.ts`. |
| DATE-002 | Add form and February views. | Submit 2024-02-29 and 2023-02-29. | Leap day accepted/included; impossible date rejected with associated error/focus and no mutation. | Automated unit dates/UI monthly tests; Chromium `core.spec.ts`. |
| DATE-003 | Viewing 2026-10. | Add future 2027-01 record. | No October effect; selected month unchanged; record/total appear only in 2027-01. | Automated unit dashboard/UI monthly tests; Chromium `core.spec.ts`. |
| DATE-004 | Non-UTC `America/Los_Angeles` browser timezone. | Repeat boundary and future-date cases. | Entered local calendar dates and month membership remain exact with no UTC shift. | Automated unit dates/dashboard tests; UI monthly tests; Chromium `core.spec.ts`. |
| MONEY-001 | Empty month/categories; also non-English locale. | Render normal dashboard. | Every applicable zero renders `$0.00`, identically under en-US and de-DE. | Automated unit dashboard test; Chromium `core.spec.ts`. |
| MONEY-002 | Exact amount fixtures. | Render 123456 cents and 1, 10, 99 cent values; sum integers. | `$1,234.56` and fractional-cent-boundary values exact; no floating-point drift. | Automated unit money test; Chromium `core.spec.ts`. |
| MONEY-003 | Normal and demo records/summaries/delete dialog under en-US and de-DE. | Render transactions, totals, and deletion identity. | All locations use identical fixed en-US USD with `$`, grouping, and two decimals; demo values exactly match DEMO-002. | Automated UI delete test; Chromium `core.spec.ts`, `edit-delete.spec.ts`, and `demo.spec.ts` in both locales. |
| MONEY-004 | Every accepted AMOUNT-001–003 input and all 1,000 SCALE records. | Parse, save JSON, reload, and inspect generated amounts. | Every accepted value round-trips as its expected integer-cent JSON number; every SCALE amount is an exact safe integer; no silent rounding. | Automated unit money and storage write tests; `scaleData.test.ts`; Chromium SCALE-001. |
| OVERFLOW-001 | 90,072 unique same-month/category records at 99999999999 cents. | Calculate/render summaries. | Unsafe monthly/category totals become visible/announced unavailable errors; no clamped/wrapped/rounded total and records unchanged. | Automated unit dashboard and UI monthly tests; Chromium `accessibility.spec.ts` and `responsive.spec.ts`. |
| FILTER-001 | October fixture contains all five categories and durable raw JSON. | Select each category, then all. | Exact membership for every category; unfiltered monthly/category summaries and raw collection unchanged; all restores five records. | Automated unit `dashboard.list.test.ts`; UI `transactionPreferences.test.tsx`; Chromium `transaction-list.spec.ts`; production filter. |
| FILTER-002 | Nonempty month without transport; then clear filter. | Select absent category and activate Clear filter. | Distinct non-error no-match message; unchanged summaries; restored list/result announcement and Category-filter focus. | Automated unit list/UI preference tests; Chromium `transaction-list.spec.ts`. |
| SORT-001 | `tie-a`/`tie-b` 200 cents, `tie-c` 100 cents on 2026-10-10, plus older/newer records. | Date ascending and descending. | Exact local-date order; every same-date group ID ascending; summaries/raw data unchanged. | Automated unit list/UI preference tests; Chromium parameterized `transaction-list.spec.ts`. |
| SORT-002 | Same tie fixture. | Amount ascending and descending. | Exact-cent order `older,tie-c,newer,tie-a,tie-b` and reverse by amount with ties still ID ascending; summaries/raw data unchanged. | Automated unit list/UI preference tests; Chromium parameterized `transaction-list.spec.ts`; production amount sort. |
| EMPTY-001 | Month has no records. | Select empty month and activate Add expense for this month. | Distinct non-error empty-month message; add task opens with Amount focused. | Automated UI preference test; Chromium `transaction-list.spec.ts`. |
| EMPTY-002 | Compare empty-month and no-match states. | Inspect both messages/actions. | States and actions are distinct; neither is presented as an error. | Automated UI preference test; Chromium `transaction-list.spec.ts`. |
| DELETE-001 | Identified expense with known amount/category/date. | Open dialog by keyboard; Tab and Shift+Tab. | Exact identity/consequence/no-undo text, accessible dialog, Cancel initial focus, contained visible focus. | Automated UI `deleteExpense.test.tsx`; Chromium `edit-delete.spec.ts`; manual keyboard/native-dialog review. |
| DELETE-002 | Same target and known raw value. | Cancel and separately Escape. | No mutation or write; dialog closes and Delete requester regains focus. | Automated UI parameterized test; Chromium `edit-delete.spec.ts`; production Cancel/Escape review. |
| DELETE-003 | Variants with following, preceding-only, and no remaining result, including filtered amount sorts. | Confirm deletion. | Only target removed within 2 seconds and summaries recalculated; focus goes to next visible edit, previous visible edit, or Add expense respectively; no undo. | Automated UI delete tests; Chromium `edit-delete.spec.ts` and `transaction-list.spec.ts`. |
| DELETE-004 | Target exists; write failure injected. | Confirm deletion and reload. | Removal/warning only in memory before reload; durable target/raw collection restored afterward. | Automated Chromium `edit-delete.spec.ts`; detailed PERSIST-010 row. |
| DELETE-005 | Food filter active with other October records hidden; one visible result. | Confirm deletion of last visible result. | Visible result/summaries update within 2 seconds; no-match announcement; Clear filter focused rather than Add expense; hidden month data intact. | Automated UI preference test; Chromium `transaction-list.spec.ts`. |
| DEMO-001 | Fresh normal/demo destinations. | Open all eight specified exact/case/repeated/unrelated query variants. | Only `?demo=1`, `?source=x&demo=1`, and `?demo=1&demo=0` activate; first exact case-sensitive value controls. | Automated unit `demoData.test.ts`; UI `demoMode.test.tsx`; Chromium `demo.spec.ts`. |
| DEMO-002 | Fresh demo under en-US and de-DE. | Compare all records, October selection, summaries, default order, and deletion formatting. | Exact ten-record baseline; total `$1,732.65`; category totals `$122.75/$50.90/$1,450.00/$24.00/$85.00`; IDs 008→001; fixed USD in both locales. | Automated unit `demoData.test.ts`; Chromium `demo.spec.ts`. |
| DEMO-003 | Fresh labeled demo with instrumented populated real storage. | Add, invalid add, edit, delete, adjacent months, filter, sort; fresh reload. | All interactions work in demo memory; fresh activation restores exact baseline/month/defaults/form/status; fictional label present; zero real-storage activity. | Automated UI `demoMode.test.tsx`; Chromium `demo.spec.ts`. |
| DEMO-004 | Modified normal and demo records/view state, open dialog and form. | URL navigation, reload, back, forward. | Fresh destination state each time; no records, month, preferences, form, dialog, or status leaks across modes. | Automated UI `demoMode.test.tsx`; Chromium `demo.spec.ts`. |
| DEMO-005 | Populated, missing, readable malformed, and read-throwing real storage instrumented before initialization. | Initialize demo, perform all DEMO-003 interactions, reload in each precondition. | For every precondition, zero storage reads, writes/clears/removals, and listener registrations; no real recovery/success claim. | Automated Chromium parameterized `demo.spec.ts`. |
| DEMO-006 | Concurrent normal tab with known real data; both listener registration forms instrumented. | Perform demo interactions and return to normal tab. | Demo neither reacts to nor causes real-storage events; all three isolation counters remain zero; normal tab unchanged. | Automated Chromium `demo.spec.ts`. |
| DEMO-007 | Known readable normal raw value and modified demo state. | Return via URL/history and concurrent normal tab. | No demo content appears; known real record restored and raw value byte-for-byte unchanged. | Automated Chromium `demo.spec.ts` with DEMO-004/006. |
| A11Y | Every UI-contract core-flow state at desktop/320px, 200% zoom/text resize, keyboard-only flows, and required assistive review. | Automated axe/observable checks plus keyboard, visual, responsive, and VoiceOver methods. | Automated, keyboard, and visual/responsive checks pass with zero reported automated AA violations and measured targets ≥24px. VoiceOver review is not complete; overall A11Y/FR-025/SC-007 gate remains open. | Automated Chromium `accessibility.spec.ts` and `responsive.spec.ts`; manual keyboard/responsive review; no screen-reader evidence. |
| SCALE fixture | Integer formula for IDs `scale-0001`–`scale-1000`. | Generate and independently inspect 1,000 records and summaries. | Exact ID order, amount/category/date/note formulas, integer cents, 100 records per month January–October, 200 per category, exact independent summaries. | Automated unit `scaleData.test.ts`. |
| SCALE-001 | Sealed valid 1,000-record version-1 envelope. | Reload and inspect every record and January–October view. | All 1,000 records and every amount/summary exactly match independent expectations. | Automated Chromium `scale.spec.ts`. |
| SCALE-002 | Fresh loaded SCALE state at desktop and mobile layouts. | Three repetitions each of add, same/cross-month edit, delete, month selection, five filters, and four sort directions. | 45 interactions per layout produced exact visible results, each from committed activation in under 2 seconds. | Automated Chromium `scale.spec.ts`. |

## Requirement-to-evidence audit

Every mapped case has its detailed precondition, input, actual outcome, evidence method, and shared reference-Chromium version in the inventories above. No FR-001–FR-029 mapping is unlisted.

| Requirement | Mapped cases and audit outcome |
| --- | --- |
| FR-001 add expense | CORE-001 and DEMO-003 pass. |
| FR-002 five categories | CORE-003 passes for all five valid categories and invalid-category rejection. |
| FR-003 amount validation | AMOUNT-001–008 pass in add and edit; A11Y automated/keyboard error associations pass, subject to the open VoiceOver method. |
| FR-004 local dates | DATE-001–004 pass, including leap day and non-UTC timezone. |
| FR-005 optional notes | CORE-004 passes in add/edit and exact persistence. |
| FR-006 shared add/edit validation | Every AMOUNT-001–008 row passes in both forms. |
| FR-007 editing | CORE-005 and CORE-006 pass; AMOUNT rejection precondition passes in edit. |
| FR-008 confirmed deletion | DELETE-001–003 and DELETE-005 pass. |
| FR-009 deletion identity and safe focus | DELETE-001 and MONEY-003 pass. |
| FR-010 deletion durability | DELETE-002–004 and PERSIST-010 pass. |
| FR-011 month selection/default | CORE-002 and DATE-001 pass, including empty-native-month regression. |
| FR-012 monthly dashboard | CORE-001, CORE-003, and DEMO-002 pass. |
| FR-013 exact month membership | CORE-005 and DATE-001–004 pass. |
| FR-014 integer cents, formatting, overflow | AMOUNT-003/005/008, MONEY-001–004, OVERFLOW-001, SCALE fixture, and SCALE-001 pass. |
| FR-015 updates within 2 seconds | SCALE-002 and DELETE-003/005 timing pass. |
| FR-016 category filter | FILTER-001 and FILTER-002 pass. |
| FR-017 unfiltered summaries | FILTER-001/002 and SORT-002 pass. |
| FR-018 exact sorting and ties | SORT-001/002 and DEMO-002 pass. |
| FR-019 non-mutating list operations | FILTER-001 and SORT-001/002 pass with source/raw assertions. |
| FR-020 reload persistence | PERSIST-002 and SCALE-001 pass. |
| FR-021 storage classification | PERSIST-001–007 each pass with case-level outcomes above. |
| FR-022 guarded replacement | RECOVERY-001–007 each pass; A11Y dialog automated/keyboard evidence passes, subject to the open VoiceOver method. |
| FR-023 failed writes and retained work | PERSIST-008–013 and DELETE-004 pass, including post-failure reload outcomes. |
| FR-024 distinct empty states/focus | EMPTY-001/002 and FILTER-002 pass. |
| FR-025 WCAG-oriented core flows | A11Y automated, keyboard, visual, and responsive evidence passes; VoiceOver review remains open, so the complete FR-025/SC-007 gate is not claimed. |
| FR-026 dialog and post-mutation focus | CORE-005/006, DELETE-001–003/005, RECOVERY-001–007, and A11Y keyboard checks pass; CORE-006 resorting stabilization is recorded above. |
| FR-027 exact demo activation/transitions | DEMO-001 and DEMO-004 pass. |
| FR-028 deterministic demo baseline | DEMO-002 and DEMO-003 pass. |
| FR-029 demo storage isolation | DEMO-003/005/006/007 pass with zero read/write/listener counters under all specified preconditions. |

SC-001 was not measured because no first-time-user study was conducted. Other browsers, including Firefox and WebKit/Safari, were not tested and are not claimed as verified. All mapped functional requirements have recorded objective evidence, subject to the explicit VoiceOver limitation above.

## Remaining gate

- T047 remains unchecked because the VoiceOver portion and complete manual accessibility gate are not complete.
- T048 remains complete; T055 now records its PERSIST-001–013 and RECOVERY-001–007 case-level evidence.
- T049 remains complete; T056 now records every mapped case's evidence details and preserves the open A11Y limitation.
- T050 remains open because the VoiceOver review and complete accessibility gate are unresolved. The passing automated sequence does not satisfy the missing manual screen-reader evidence.
- T051 is complete: invalid/empty Month input preserves the last valid selection.
- T052 and T054 were not executed in this convergence work.
- T053 is complete: the intermittent failure was reproduced, its demonstrated draft-initialization race was corrected without weakening assertions, and affected plus complete checks passed.

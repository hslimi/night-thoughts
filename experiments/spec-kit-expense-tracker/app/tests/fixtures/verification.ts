export const QUICKSTART_CASE_SETS = {
  AMOUNT: [
    'AMOUNT-001',
    'AMOUNT-002',
    'AMOUNT-003',
    'AMOUNT-004',
    'AMOUNT-005',
    'AMOUNT-006',
    'AMOUNT-007',
    'AMOUNT-008',
  ],
  CORE: [
    'CORE-001',
    'CORE-002',
    'CORE-003',
    'CORE-004',
    'CORE-005',
    'CORE-006',
  ],
  DATE: ['DATE-001', 'DATE-002', 'DATE-003', 'DATE-004'],
  MONEY: ['MONEY-001', 'MONEY-002', 'MONEY-003', 'MONEY-004'],
  OVERFLOW: ['OVERFLOW-001'],
  FILTER: ['FILTER-001', 'FILTER-002'],
  SORT: ['SORT-001', 'SORT-002'],
  EMPTY: ['EMPTY-001', 'EMPTY-002'],
  DELETE: [
    'DELETE-001',
    'DELETE-002',
    'DELETE-003',
    'DELETE-004',
    'DELETE-005',
  ],
  PERSIST: [
    'PERSIST-001',
    'PERSIST-002',
    'PERSIST-003',
    'PERSIST-004',
    'PERSIST-005',
    'PERSIST-006',
    'PERSIST-007',
    'PERSIST-008',
    'PERSIST-009',
    'PERSIST-010',
    'PERSIST-011',
    'PERSIST-012',
    'PERSIST-013',
  ],
  RECOVERY: [
    'RECOVERY-001',
    'RECOVERY-002',
    'RECOVERY-003',
    'RECOVERY-004',
    'RECOVERY-005',
    'RECOVERY-006',
    'RECOVERY-007',
  ],
  DEMO: [
    'DEMO-001',
    'DEMO-002',
    'DEMO-003',
    'DEMO-004',
    'DEMO-005',
    'DEMO-006',
    'DEMO-007',
  ],
  A11Y: ['A11Y'],
  SCALE: ['SCALE-001', 'SCALE-002'],
} as const;

export type QuickstartCaseId =
  (typeof QUICKSTART_CASE_SETS)[keyof typeof QUICKSTART_CASE_SETS][number];

export interface AutomatedVerificationResult {
  caseId: QuickstartCaseId;
  precondition: string;
  input: string;
  actualOutcome: string;
}

export function formatVerificationResult({
  caseId,
  precondition,
  input,
  actualOutcome,
}: AutomatedVerificationResult): string {
  return [
    `[${caseId}]`,
    `Precondition: ${precondition}`,
    `Input: ${input}`,
    `Actual outcome: ${actualOutcome}`,
  ].join('\n');
}

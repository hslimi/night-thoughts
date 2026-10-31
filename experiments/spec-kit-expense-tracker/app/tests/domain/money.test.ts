import { describe, expect, it } from 'vitest';
import {
  MAX_AMOUNT_CENTS,
  formatUSD,
  parseAmount,
} from '../../src/domain/money';

const acceptedAmounts = [
  ['AMOUNT-001', '1', 100],
  ['AMOUNT-001', '1.2', 120],
  ['AMOUNT-001', '1.23', 123],
  ['AMOUNT-002', '  001.2  ', 120],
  ['AMOUNT-002', '000.50', 50],
  ['AMOUNT-002', '.50', 50],
  ['AMOUNT-003', '0.01', 1],
  ['AMOUNT-003', '999999999.99', 99999999999],
] as const;

const rejectedAmounts = [
  ['AMOUNT-004', ''],
  ['AMOUNT-004', '   '],
  ['AMOUNT-004', '0'],
  ['AMOUNT-004', '0.00'],
  ['AMOUNT-004', '000'],
  ['AMOUNT-004', '-1'],
  ['AMOUNT-005', '.'],
  ['AMOUNT-005', '1.'],
  ['AMOUNT-005', '1.234'],
  ['AMOUNT-006', '1,000'],
  ['AMOUNT-006', '$1'],
  ['AMOUNT-006', '+1'],
  ['AMOUNT-006', '1e2'],
  ['AMOUNT-007', 'abc'],
  ['AMOUNT-007', 'NaN'],
  ['AMOUNT-007', 'Infinity'],
  ['AMOUNT-008', '1000000000.00'],
  ['AMOUNT-008', '1000000000'],
] as const;

describe('exact money parsing', () => {
  it.each(acceptedAmounts)(
    '%s and MONEY-004: parses %j directly as %i integer cents',
    (_caseId, input, expectedCents) => {
      expect(parseAmount(input)).toEqual({
        ok: true,
        amountCents: expectedCents,
      });
    },
  );

  it.each(rejectedAmounts)(
    '%s: rejects %j without rounding or conversion',
    (_caseId, input) => {
      const result = parseAmount(input);
      expect(result.ok).toBe(false);
      if (result.ok) {
        throw new Error(`Unexpected accepted amount: ${result.amountCents}`);
      }
    },
  );

  it('MONEY-002: keeps fractional-cent-boundary inputs exact', () => {
    expect(parseAmount('0.01')).toEqual({ ok: true, amountCents: 1 });
    expect(parseAmount('0.10')).toEqual({ ok: true, amountCents: 10 });
    expect(parseAmount('0.99')).toEqual({ ok: true, amountCents: 99 });
    expect(parseAmount('1234.56')).toEqual({
      ok: true,
      amountCents: 123456,
    });
  });

  it('defines the maximum as exactly 99999999999 cents', () => {
    expect(MAX_AMOUNT_CENTS).toBe(99999999999);
  });
});

describe('fixed en-US USD formatting', () => {
  it.each([
    [0, '$0.00'],
    [1, '$0.01'],
    [10, '$0.10'],
    [99, '$0.99'],
    [123456, '$1,234.56'],
    [99999999999, '$999,999,999.99'],
  ])('MONEY-001/002: formats %i cents as %s', (cents, expected) => {
    expect(formatUSD(cents)).toBe(expected);
  });
});

import { describe, expect, it } from 'vitest';
import { buildFixedLocalClock } from '../fixtures/expenses';
import {
  getCurrentLocalMonth,
  isLocalDate,
  isMonth,
  monthForDate,
} from '../../src/domain/dates';

describe('local calendar dates', () => {
  it.each([
    '2024-02-29',
    '2026-02-28',
    '2026-04-30',
    '2026-10-01',
    '2026-10-31',
    '2027-01-01',
    '1999-12-31',
  ])('DATE-001/002/003: accepts exact real local date %s', (date) => {
    expect(isLocalDate(date)).toBe(true);
  });

  it.each([
    '',
    '2023-02-29',
    '2026-02-29',
    '2026-04-31',
    '2026-13-01',
    '2026-00-01',
    '2026-01-00',
    '2026-01-32',
    '2026-2-09',
    '26-02-09',
    '2026/02/09',
    '2026-02-09T00:00:00Z',
    null,
    20260209,
  ])('DATE-002: rejects missing, impossible, or inexact date %j', (date) => {
    expect(isLocalDate(date)).toBe(false);
  });

  it('DATE-001/004: derives months lexically without UTC conversion', () => {
    expect(monthForDate('2026-09-30')).toBe('2026-09');
    expect(monthForDate('2026-10-01')).toBe('2026-10');
    expect(monthForDate('2026-10-31')).toBe('2026-10');
    expect(monthForDate('2026-11-01')).toBe('2026-11');
    expect(() => monthForDate('2023-02-29')).toThrow(/valid local date/i);
  });

  it.each(['2026-01', '2026-10', '2027-12'])(
    'accepts exact month %s',
    (month) => {
      expect(isMonth(month)).toBe(true);
    },
  );

  it.each(['2026-1', '2026-00', '2026-13', '2026-10-01', '']) (
    'rejects invalid month %s',
    (month) => {
      expect(isMonth(month)).toBe(false);
    },
  );

  it('CORE-002: derives the initial month from local getters', () => {
    expect(getCurrentLocalMonth(buildFixedLocalClock(2026, 10, 31))).toBe(
      '2026-10',
    );
    expect(getCurrentLocalMonth(buildFixedLocalClock(2027, 1, 1))).toBe(
      '2027-01',
    );
  });
});

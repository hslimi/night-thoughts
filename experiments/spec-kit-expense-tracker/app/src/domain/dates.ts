export type LocalDateString = string;
export type MonthString = string;

const DATE_PATTERN = /^(\d{4})-(\d{2})-(\d{2})$/;
const MONTH_PATTERN = /^(\d{4})-(\d{2})$/;

function isLeapYear(year: number): boolean {
  return year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
}

function daysInMonth(year: number, month: number): number {
  if (month === 2) {
    return isLeapYear(year) ? 29 : 28;
  }
  return [4, 6, 9, 11].includes(month) ? 30 : 31;
}

export function isLocalDate(value: unknown): value is LocalDateString {
  if (typeof value !== 'string') {
    return false;
  }
  const match = DATE_PATTERN.exec(value);
  if (!match) {
    return false;
  }
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  return month >= 1 && month <= 12 && day >= 1 && day <= daysInMonth(year, month);
}

export function isMonth(value: unknown): value is MonthString {
  if (typeof value !== 'string') {
    return false;
  }
  const match = MONTH_PATTERN.exec(value);
  if (!match) {
    return false;
  }
  const month = Number(match[2]);
  return month >= 1 && month <= 12;
}

export function monthForDate(date: string): MonthString {
  if (!isLocalDate(date)) {
    throw new Error('Expected a valid local date');
  }
  return date.slice(0, 7);
}

function pad(value: number): string {
  return String(value).padStart(2, '0');
}

export function getCurrentLocalMonth(now = new Date()): MonthString {
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}`;
}

export function getCurrentLocalDate(now = new Date()): LocalDateString {
  return `${getCurrentLocalMonth(now)}-${pad(now.getDate())}`;
}

export const MAX_AMOUNT_CENTS = 99999999999;

const AMOUNT_PATTERN = /^(?:\d+(?:\.\d{1,2})?|\.\d{1,2})$/;
const USD_FORMATTER = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

export type AmountParseResult =
  | { ok: true; amountCents: number }
  | { ok: false; error: 'invalid-amount' };

export function parseAmount(input: string): AmountParseResult {
  const normalized = input.trim();
  if (!AMOUNT_PATTERN.test(normalized)) {
    return { ok: false, error: 'invalid-amount' };
  }

  const [wholePart = '', fractionPart = ''] = normalized.split('.');
  const amountCents = Number(
    `${wholePart || '0'}${fractionPart.padEnd(2, '0')}`,
  );
  if (
    !Number.isSafeInteger(amountCents) ||
    amountCents < 1 ||
    amountCents > MAX_AMOUNT_CENTS
  ) {
    return { ok: false, error: 'invalid-amount' };
  }

  return { ok: true, amountCents };
}

export function formatUSD(cents: number): string {
  return USD_FORMATTER.format(cents / 100);
}

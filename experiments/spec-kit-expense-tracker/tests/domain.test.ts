import { describe, expect, it } from "vitest";
import { CATEGORIES } from "../src/expenses/model";
import type { Expense } from "../src/expenses/model";
import {
  calculateMonthlySummary,
  currentLocalMonth,
  isCategory,
  isValidDate,
  normalizeNote,
  parseAmountToCents,
  selectMonthlyExpenses,
} from "../src/expenses/domain";

describe("expense input validation", () => {
  it.each([
    ["1", 100],
    ["1.2", 120],
    ["1.20", 120],
    ["0.01", 1],
    ["100000.00", 10_000_000],
  ])("converts %s to exact integer cents", (input, cents) => {
    expect(parseAmountToCents(input)).toBe(cents);
  });

  it.each([
    "",
    "0",
    "0.00",
    "-1",
    "+1",
    " 1",
    "1 ",
    "1,000",
    "$1",
    "1e2",
    "one",
    "1.001",
    "100000.01",
  ])("rejects unsupported amount %j", (input) => {
    expect(parseAmountToCents(input)).toBeNull();
  });

  it("accepts only the five supported categories", () => {
    expect(CATEGORIES).toEqual([
      "food",
      "transport",
      "housing",
      "entertainment",
      "other",
    ]);
    expect(CATEGORIES.every(isCategory)).toBe(true);
    expect(isCategory("travel")).toBe(false);
    expect(isCategory("")).toBe(false);
  });

  it("accepts real YYYY-MM-DD calendar dates and future dates", () => {
    expect(isValidDate("2024-02-29")).toBe(true);
    expect(isValidDate("2999-12-31")).toBe(true);
    expect(isValidDate("2023-02-29")).toBe(false);
    expect(isValidDate("2024-13-01")).toBe(false);
    expect(isValidDate("2024-2-01")).toBe(false);
    expect(isValidDate("2024-04-31")).toBe(false);
  });

  it("trims notes and omits empty notes", () => {
    expect(normalizeNote("  lunch with team  ")).toBe("lunch with team");
    expect(normalizeNote("   ")).toBeUndefined();
    expect(normalizeNote(undefined)).toBeUndefined();
  });
});

function expense(
  id: string,
  amountCents: number,
  category: Expense["category"],
  date: string,
): Expense {
  return { id, amountCents, category, date };
}

describe("monthly expense selectors", () => {
  const expenses = [
    expense("food-a", 1200, "food", "2026-11-02"),
    expense("transport", 3300, "transport", "2026-11-03"),
    expense("food-b", 1200, "food", "2026-11-03"),
    expense("last-month", 900, "other", "2026-10-31"),
  ];

  it("calculates month and category totals with zeroes for unused categories", () => {
    expect(calculateMonthlySummary(expenses, "2026-11")).toEqual({
      totalCents: 5700,
      categoryTotals: {
        food: 2400,
        transport: 3300,
        housing: 0,
        entertainment: 0,
        other: 0,
      },
    });
  });

  it("returns exact totals at the safe-integer boundary and reports overflow", () => {
    const atLimit = [
      expense("near-limit", Number.MAX_SAFE_INTEGER - 1, "food", "2026-11-01"),
      expense("last-cent", 1, "food", "2026-11-02"),
    ];
    const overLimit = [
      ...atLimit,
      expense("overflow-cent", 1, "food", "2026-11-03"),
    ];

    expect(calculateMonthlySummary(atLimit, "2026-11").totalCents).toBe(
      Number.MAX_SAFE_INTEGER,
    );
    expect(calculateMonthlySummary(overLimit, "2026-11")).toEqual({
      totalCents: null,
      categoryTotals: {
        food: null,
        transport: 0,
        housing: 0,
        entertainment: 0,
        other: 0,
      },
    });
  });

  it("filters by local YYYY-MM and category, then stably sorts both fields", () => {
    expect(
      selectMonthlyExpenses(expenses, "2026-11", "food", "date", "descending").map(
        ({ id }) => id,
      ),
    ).toEqual(["food-b", "food-a"]);
    expect(
      selectMonthlyExpenses(expenses, "2026-11", "all", "amount", "descending").map(
        ({ id }) => id,
      ),
    ).toEqual(["transport", "food-a", "food-b"]);
    expect(
      selectMonthlyExpenses(expenses, "2026-11", "all", "amount", "ascending").map(
        ({ id }) => id,
      ),
    ).toEqual(["food-a", "food-b", "transport"]);
  });

  it("uses local year and month when selecting the current month", () => {
    const localDate = new Date(2026, 10, 3, 23, 45);
    expect(currentLocalMonth(localDate)).toBe("2026-11");
  });
});

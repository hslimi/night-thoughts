import type { Expense } from "./model";

export const DEMO_EXPENSES: Expense[] = [
  {
    id: "demo-coffee",
    amountCents: 525,
    category: "food",
    date: "2026-11-03",
    note: "Coffee",
  },
  {
    id: "demo-transit",
    amountCents: 3200,
    category: "transport",
    date: "2026-11-02",
    note: "Transit pass",
  },
  {
    id: "demo-rent",
    amountCents: 145000,
    category: "housing",
    date: "2026-10-01",
    note: "Rent",
  },
];

export const CATEGORIES = [
  "food",
  "transport",
  "housing",
  "entertainment",
  "other",
] as const;

export type Category = (typeof CATEGORIES)[number];
export type CategoryFilter = Category | "all";
export type SortField = "date" | "amount";
export type SortDirection = "ascending" | "descending";

export interface Expense {
  id: string;
  amountCents: number;
  category: Category;
  date: string;
  note?: string;
}

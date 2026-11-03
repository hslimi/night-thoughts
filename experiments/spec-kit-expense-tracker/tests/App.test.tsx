import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "../src/App";
import { EXPENSES_STORAGE_KEY } from "../src/expenses/persistence";
import type { Category, Expense } from "../src/expenses/model";
import * as expenseDomain from "../src/expenses/domain";

beforeEach(() => {
  vi.restoreAllMocks();
  window.history.replaceState({}, "", "/");
  window.localStorage.clear();
});

afterEach(() => {
  cleanup();
});

function dateForMonth(monthOffset: number, day: number): string {
  const date = new Date();
  date.setDate(1);
  date.setMonth(date.getMonth() + monthOffset);
  date.setDate(day);
  return [
    String(date.getFullYear()).padStart(4, "0"),
    String(date.getMonth() + 1).padStart(2, "0"),
    String(date.getDate()).padStart(2, "0"),
  ].join("-");
}

function monthForDate(date: string): string {
  return date.slice(0, 7);
}

function saveExpenses(expenses: Expense[]) {
  window.localStorage.setItem(
    EXPENSES_STORAGE_KEY,
    JSON.stringify({ version: 1, expenses }),
  );
}

function expense(
  id: string,
  amountCents: number,
  category: Category,
  date: string,
  note: string,
): Expense {
  return { id, amountCents, category, date, note };
}

describe("App", () => {
  it("renders the expense tracker", () => {
    render(<App />);
    expect(screen.getByRole("heading", { name: /expense tracker/i })).toBeInTheDocument();
  });

  it("creates an expense with the keyboard and persists its details", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.tab();
    await user.tab();
    const amount = screen.getByRole("textbox", { name: /amount/i });
    expect(amount).toHaveFocus();
    await user.type(amount, "12.50");
    await user.tab();
    await user.tab();
    await user.tab();
    await user.type(screen.getByRole("textbox", { name: /note/i }), "Lunch");
    await user.tab();
    await user.keyboard("{Enter}");

    expect(await screen.findByText("Lunch")).toBeInTheDocument();
    expect(
      within(screen.getByRole("list", { name: /expenses/i })).getByText("$12.50"),
    ).toBeInTheDocument();
    expect(JSON.parse(window.localStorage.getItem(EXPENSES_STORAGE_KEY) ?? "null")).toEqual({
      version: 1,
      expenses: [
        expect.objectContaining({
          amountCents: 1250,
          category: "food",
          note: "Lunch",
        }),
      ],
    });
  });

  it("announces invalid input and does not persist it", async () => {
    const user = userEvent.setup();
    render(<App />);
    await user.type(screen.getByRole("textbox", { name: /amount/i }), "100000.01");
    await user.click(screen.getByRole("button", { name: /add expense/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/amount/i);
    expect(window.localStorage.getItem(EXPENSES_STORAGE_KEY)).toBeNull();
  });

  it("announces a load failure and retries without substituting a durable empty collection", async () => {
    const user = userEvent.setup();
    vi.spyOn(Storage.prototype, "getItem").mockImplementationOnce(() => {
      throw new Error("storage unavailable");
    });
    render(<App />);

    expect(await screen.findByRole("alert")).toHaveTextContent(/could not load/i);
    await user.click(screen.getByRole("button", { name: /retry loading/i }));
    expect(await screen.findByRole("heading", { name: /expense tracker/i })).toBeInTheDocument();
    expect(screen.queryByText(/could not load/i)).not.toBeInTheDocument();
    expect(window.localStorage.getItem(EXPENSES_STORAGE_KEY)).toBeNull();
  });

  it("keeps a failed save visible and retains the expense in the current view", async () => {
    const user = userEvent.setup();
    vi.spyOn(Storage.prototype, "setItem").mockImplementationOnce(() => {
      throw new Error("quota exceeded");
    });
    render(<App />);
    await user.type(screen.getByRole("textbox", { name: /amount/i }), "8.75");
    await user.click(screen.getByRole("button", { name: /add expense/i }));

    expect(await screen.findByText(/not saved/i)).toBeInTheDocument();
    expect(
      within(screen.getByRole("list", { name: /expenses/i })).getByText("$8.75"),
    ).toBeInTheDocument();
    expect(window.localStorage.getItem(EXPENSES_STORAGE_KEY)).toBeNull();
  });

  it("requires informed confirmation before replacing malformed saved data", async () => {
    const user = userEvent.setup();
    window.localStorage.setItem(EXPENSES_STORAGE_KEY, "{malformed");
    vi.spyOn(window, "confirm").mockReturnValue(true);
    render(<App />);

    expect(await screen.findByRole("alert")).toHaveTextContent(/malformed/i);
    await user.click(screen.getByRole("button", { name: /start fresh/i }));
    expect(window.confirm).toHaveBeenCalledWith(
      expect.stringMatching(/replace.*malformed.*clear.*current/i),
    );
    expect(window.localStorage.getItem(EXPENSES_STORAGE_KEY)).toBe(
      JSON.stringify({ version: 1, expenses: [] }),
    );
  });

  it("keeps demo mode isolated from storage and resets its fictional data on reload", async () => {
    const user = userEvent.setup();
    window.history.replaceState({}, "", "/?demo=1");
    const getItem = vi.spyOn(Storage.prototype, "getItem");
    const setItem = vi.spyOn(Storage.prototype, "setItem");
    const addEventListener = vi.spyOn(window, "addEventListener");
    const { unmount } = render(<App />);

    expect(screen.getByText(/demo mode/i)).toBeInTheDocument();
    const expenseList = screen.getByRole("list", { name: /expenses/i });
    const initialCount = within(expenseList).getAllByRole("listitem").length;
    await user.type(screen.getByRole("textbox", { name: /amount/i }), "4.50");
    await user.click(screen.getByRole("button", { name: /add expense/i }));
    expect(within(expenseList).getAllByRole("listitem")).toHaveLength(initialCount + 1);
    expect(getItem).not.toHaveBeenCalled();
    expect(setItem).not.toHaveBeenCalled();
    expect(addEventListener.mock.calls.some(([type]) => type === "storage")).toBe(false);

    unmount();
    render(<App />);
    expect(
      within(screen.getByRole("list", { name: /expenses/i })).getAllByRole("listitem"),
    ).toHaveLength(initialCount);
  });

  it("uses normal storage mode for non-exact demo query strings", async () => {
    window.history.replaceState({}, "", "/?demo=1&other=value");
    const getItem = vi.spyOn(Storage.prototype, "getItem");
    render(<App />);

    expect(screen.queryByText(/demo mode/i)).not.toBeInTheDocument();
    expect(getItem).toHaveBeenCalledWith(EXPENSES_STORAGE_KEY);
  });

  it("shows all monthly category totals independently of the transaction filter", async () => {
    const user = userEvent.setup();
    const currentMonth = dateForMonth(0, 3);
    const previousMonth = dateForMonth(-1, 15);
    saveExpenses([
      expense("food-a", 1200, "food", dateForMonth(0, 2), "Lunch"),
      expense("transport", 3300, "transport", currentMonth, "Bus"),
      expense("other-month", 900, "other", previousMonth, "Earlier"),
    ]);
    render(<App />);

    const summary = await screen.findByRole("region", { name: /monthly summary/i });
    expect(within(summary).getByText("$45.00")).toBeInTheDocument();
    const categoryTotals = within(summary).getByRole("list", {
      name: /category totals/i,
    });
    expect(within(categoryTotals).getByText("Housing")).toBeInTheDocument();
    expect(within(categoryTotals).getAllByText("$0.00").length).toBeGreaterThan(0);

    await user.selectOptions(
      screen.getByRole("combobox", { name: /filter by category/i }),
      "food",
    );
    expect(screen.getByText("Lunch")).toBeInTheDocument();
    expect(screen.queryByText("Bus")).not.toBeInTheDocument();
    expect(within(summary).getByText("$45.00")).toBeInTheDocument();
  });

  it("distinguishes an empty month from a filter with no matching transactions", async () => {
    const user = userEvent.setup();
    saveExpenses([
      expense("food", 1200, "food", dateForMonth(0, 2), "Lunch"),
    ]);
    render(<App />);

    const monthPicker = screen.getByLabelText("Month");
    fireEvent.change(monthPicker, { target: { value: "2001-01" } });
    expect(await screen.findByText(/no expenses for this month/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /add an expense/i })).toBeInTheDocument();

    fireEvent.change(monthPicker, { target: { value: monthForDate(dateForMonth(0, 2)) } });
    await user.selectOptions(
      screen.getByRole("combobox", { name: /filter by category/i }),
      "housing",
    );
    expect(await screen.findByText(/no expenses match this category/i)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /clear category filter/i }));
    expect(screen.getByText("Lunch")).toBeInTheDocument();
  });

  it("shows a future expense only in its selected local month", async () => {
    saveExpenses([
      expense("future", 2500, "other", "2999-12-31", "Future"),
    ]);
    render(<App />);

    expect(screen.queryByText("Future")).not.toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Month"), {
      target: { value: "2999-12" },
    });
    expect(await screen.findByText("Future")).toBeInTheDocument();
  });

  it("announces unsafe monthly aggregate totals instead of displaying a rounded value", async () => {
    saveExpenses([
      expense("sample", 2500, "food", dateForMonth(0, 2), "Sample"),
    ]);
    vi.spyOn(expenseDomain, "calculateMonthlySummary").mockReturnValue({
      totalCents: null,
      categoryTotals: {
        food: null,
        transport: 0,
        housing: 0,
        entertainment: 0,
        other: 0,
      },
    });
    render(<App />);

    expect(
      (await screen.findAllByRole("alert")).some((element) =>
        element.textContent?.match(/cannot be displayed exactly/i),
      ),
    ).toBe(true);
    expect(screen.getByText(/monthly total cannot be displayed exactly/i)).toBeInTheDocument();
  });

  it("edits a record with creation-equivalent validation and updates month/category summaries", async () => {
    const user = userEvent.setup();
    saveExpenses([
      expense("editable", 1200, "food", dateForMonth(0, 2), "Lunch"),
    ]);
    render(<App />);

    await user.click(screen.getByRole("button", { name: "Edit Lunch" }));
    expect(screen.getByRole("button", { name: /save changes/i })).toBeInTheDocument();
    const amount = screen.getByRole("textbox", { name: /amount/i });
    await user.clear(amount);
    await user.type(amount, "15.00");
    await user.selectOptions(
      screen.getByRole("combobox", { name: "Category" }),
      "transport",
    );
    fireEvent.change(screen.getByLabelText("Date"), {
      target: { value: dateForMonth(1, 5) },
    });
    const note = screen.getByRole("textbox", { name: /note/i });
    await user.clear(note);
    await user.type(note, "Train");
    await user.click(screen.getByRole("button", { name: /save changes/i }));

    expect(await screen.findByText(/no expenses for this month/i)).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Month"), {
      target: { value: monthForDate(dateForMonth(1, 5)) },
    });
    expect(await screen.findByText("Train")).toBeInTheDocument();
    const summary = screen.getByRole("region", { name: /monthly summary/i });
    expect(within(summary).getAllByText("$15.00")).toHaveLength(2);
    expect(
      within(summary).getByRole("list", { name: /category totals/i }),
    ).toHaveTextContent("Transport");
  });

  it("rejects an invalid edit without changing the saved record", async () => {
    const user = userEvent.setup();
    const record = expense("unchanged", 1200, "food", dateForMonth(0, 2), "Lunch");
    saveExpenses([record]);
    const durableValue = window.localStorage.getItem(EXPENSES_STORAGE_KEY);
    render(<App />);

    await user.click(screen.getByRole("button", { name: "Edit Lunch" }));
    const amount = screen.getByRole("textbox", { name: /amount/i });
    await user.clear(amount);
    await user.type(amount, "100000.01");
    await user.click(screen.getByRole("button", { name: /save changes/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/amount/i);
    expect(
      within(screen.getByRole("list", { name: /expenses/i })).getByText("Lunch"),
    ).toBeInTheDocument();
    expect(window.localStorage.getItem(EXPENSES_STORAGE_KEY)).toBe(durableValue);
  });

  it("cancels deletion without changing data and restores focus to the invoker", async () => {
    const user = userEvent.setup();
    const record = expense("delete-me", 1800, "food", dateForMonth(0, 2), "Snack");
    saveExpenses([record]);
    render(<App />);

    const invoker = screen.getByRole("button", { name: "Delete Snack" });
    await user.click(invoker);
    const dialog = screen.getByRole("dialog", { name: /delete expense/i });
    expect(within(dialog).getByRole("button", { name: "Cancel" })).toHaveFocus();
    await user.click(within(dialog).getByRole("button", { name: "Cancel" }));

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(invoker).toHaveFocus();
    expect(JSON.parse(window.localStorage.getItem(EXPENSES_STORAGE_KEY) ?? "null")).toEqual({
      version: 1,
      expenses: [record],
    });
  });

  it("focuses the next visible edit control after a confirmed deletion", async () => {
    const user = userEvent.setup();
    saveExpenses([
      expense("newest", 3000, "food", dateForMonth(0, 3), "Newest"),
      expense("middle", 2000, "food", dateForMonth(0, 2), "Middle"),
      expense("oldest", 1000, "food", dateForMonth(0, 1), "Oldest"),
    ]);
    render(<App />);

    await user.click(screen.getByRole("button", { name: "Delete Middle" }));
    const dialog = screen.getByRole("dialog", { name: /delete expense/i });
    await user.click(within(dialog).getByRole("button", { name: "Delete" }));

    expect(await screen.findByText("Oldest")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Edit Oldest" })).toHaveFocus();
    expect(screen.queryByText("Middle")).not.toBeInTheDocument();
  });

  it("focuses the previous visible edit control when deleting the last record", async () => {
    const user = userEvent.setup();
    saveExpenses([
      expense("newest", 3000, "food", dateForMonth(0, 3), "Newest"),
      expense("middle", 2000, "food", dateForMonth(0, 2), "Middle"),
      expense("oldest", 1000, "food", dateForMonth(0, 1), "Oldest"),
    ]);
    render(<App />);

    await user.click(screen.getByRole("button", { name: "Delete Oldest" }));
    const dialog = screen.getByRole("dialog", { name: /delete expense/i });
    await user.click(within(dialog).getByRole("button", { name: "Delete" }));

    expect(await screen.findByText("Middle")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Edit Middle" })).toHaveFocus();
  });

  it("focuses Add expense after deleting the only visible record", async () => {
    const user = userEvent.setup();
    saveExpenses([
      expense("only", 3000, "food", dateForMonth(0, 2), "Only"),
    ]);
    render(<App />);

    await user.click(screen.getByRole("button", { name: "Delete Only" }));
    const dialog = screen.getByRole("dialog", { name: /delete expense/i });
    await user.click(within(dialog).getByRole("button", { name: "Delete" }));

    expect(await screen.findByText(/no expenses for this month/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Add expense" })).toHaveFocus();
  });

  it("clears the active draft when deleting the record being edited", async () => {
    const user = userEvent.setup();
    saveExpenses([
      expense("being-edited", 3000, "food", dateForMonth(0, 2), "Being edited"),
    ]);
    render(<App />);

    await user.click(screen.getByRole("button", { name: "Edit Being edited" }));
    await user.clear(screen.getByRole("textbox", { name: /amount/i }));
    await user.type(screen.getByRole("textbox", { name: /amount/i }), "99.99");
    await user.click(screen.getByRole("button", { name: "Delete Being edited" }));
    const dialog = screen.getByRole("dialog", { name: /delete expense/i });
    await user.click(within(dialog).getByRole("button", { name: "Delete" }));

    expect(await screen.findByRole("heading", { name: "Add expense" })).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: /amount/i })).toHaveValue("");
    expect(screen.getByRole("button", { name: "Add expense" })).toHaveFocus();
    expect(window.localStorage.getItem(EXPENSES_STORAGE_KEY)).toContain('"expenses":[]');
  });

  it("resets another active edit and focuses Add expense after deleting the only visible record", async () => {
    const user = userEvent.setup();
    saveExpenses([
      expense("being-edited", 1200, "transport", dateForMonth(0, 3), "Keep editing"),
      expense("delete-visible", 1800, "food", dateForMonth(0, 2), "Delete visible"),
    ]);
    render(<App />);

    await user.click(screen.getByRole("button", { name: "Edit Keep editing" }));
    await user.clear(screen.getByRole("textbox", { name: /amount/i }));
    await user.type(screen.getByRole("textbox", { name: /amount/i }), "99.99");
    await user.selectOptions(
      screen.getByRole("combobox", { name: "Filter by category" }),
      "food",
    );
    await user.click(screen.getByRole("button", { name: "Delete Delete visible" }));
    const dialog = screen.getByRole("dialog", { name: /delete expense/i });
    await user.click(within(dialog).getByRole("button", { name: "Delete" }));

    expect(await screen.findByRole("heading", { name: "Add expense" })).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: /amount/i })).toHaveValue("");
    expect(screen.getByRole("button", { name: "Add expense" })).toHaveFocus();

    await user.selectOptions(
      screen.getByRole("combobox", { name: "Filter by category" }),
      "all",
    );
    expect(screen.getByText("Keep editing")).toBeInTheDocument();
    expect(window.localStorage.getItem(EXPENSES_STORAGE_KEY)).toContain('"amountCents":1200');
  });
});

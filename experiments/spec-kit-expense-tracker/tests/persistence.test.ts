import { describe, expect, it, vi } from "vitest";
import type { Expense } from "../src/expenses/model";
import { createExpensePersistence } from "../src/expenses/persistence";

const firstExpense: Expense = {
  id: "expense-1",
  amountCents: 1250,
  category: "food",
  date: "2026-11-02",
  note: "Lunch",
};

const secondExpense: Expense = {
  id: "expense-2",
  amountCents: 2500,
  category: "transport",
  date: "2026-11-03",
};

function createStorage(initialValue: string | null = null) {
  let value = initialValue;
  const storage = {
    getItem: vi.fn((_key: string) => value),
    setItem: vi.fn((_key: string, nextValue: string) => {
      value = nextValue;
    }),
  };
  return {
    storage,
    get value() {
      return value;
    },
  };
}

describe("expense persistence", () => {
  it("loads and validates a version-1 expense envelope", () => {
    const raw = JSON.stringify({ version: 1, expenses: [firstExpense] });
    const { storage } = createStorage(raw);
    const persistence = createExpensePersistence(storage);

    expect(persistence.load()).toEqual({
      kind: "loaded",
      expenses: [firstExpense],
    });
  });

  it("preserves malformed JSON and invalid records without accepting them", () => {
    for (const raw of [
      "{invalid",
      JSON.stringify({ version: 1, expenses: [{ ...firstExpense, amountCents: 0 }] }),
    ]) {
      const { storage } = createStorage(raw);
      const persistence = createExpensePersistence(storage);

      expect(persistence.load()).toEqual({ kind: "malformed", raw });
      expect(persistence.save([firstExpense])).toEqual({ kind: "blocked" });
      expect(storage.setItem).not.toHaveBeenCalled();
    }
  });

  it("surfaces read failures and supports retrying the same load", () => {
    const raw = JSON.stringify({ version: 1, expenses: [firstExpense] });
    const { storage } = createStorage(raw);
    vi.spyOn(storage, "getItem")
      .mockImplementationOnce(() => {
        throw new Error("storage unavailable");
      });
    const persistence = createExpensePersistence(storage);

    expect(persistence.load()).toMatchObject({ kind: "error" });
    expect(persistence.load()).toEqual({
      kind: "loaded",
      expenses: [firstExpense],
    });
  });

  it("reports failures when accessing the browser storage object itself", () => {
    const descriptor = Object.getOwnPropertyDescriptor(window, "localStorage");
    Object.defineProperty(window, "localStorage", {
      configurable: true,
      get() {
        throw new Error("storage access denied");
      },
    });

    try {
      expect(createExpensePersistence().load()).toMatchObject({ kind: "error" });
    } finally {
      if (descriptor) {
        Object.defineProperty(window, "localStorage", descriptor);
      } else {
        Reflect.deleteProperty(window, "localStorage");
      }
    }
  });

  it("leaves durable data unchanged after a failed write and saves the full collection after recovery", () => {
    const durableValue = JSON.stringify({ version: 1, expenses: [firstExpense] });
    const memory = createStorage(durableValue);
    const { storage } = memory;
    vi.spyOn(storage, "setItem").mockImplementationOnce(() => {
      throw new Error("quota exceeded");
    });
    const persistence = createExpensePersistence(storage);
    expect(persistence.load()).toMatchObject({ kind: "loaded" });

    expect(persistence.save([firstExpense, secondExpense])).toMatchObject({
      kind: "error",
    });
    expect(memory.value).toBe(durableValue);
    expect(persistence.save([firstExpense, secondExpense])).toEqual({
      kind: "saved",
    });
    expect(memory.value).toBe(
      JSON.stringify({ version: 1, expenses: [firstExpense, secondExpense] }),
    );
  });

  it("starts fresh by writing an empty v1 envelope", () => {
    const malformedValue = "not json";
    const memory = createStorage(malformedValue);
    const { storage } = memory;
    const persistence = createExpensePersistence(storage);
    expect(persistence.load()).toEqual({
      kind: "malformed",
      raw: malformedValue,
    });

    expect(persistence.startFresh()).toEqual({ kind: "saved" });
    expect(memory.value).toBe(JSON.stringify({ version: 1, expenses: [] }));
    expect(persistence.save([firstExpense])).toEqual({ kind: "saved" });
  });

  it("preserves malformed data when starting fresh fails", () => {
    const malformedValue = "not json";
    const memory = createStorage(malformedValue);
    const { storage } = memory;
    vi.spyOn(storage, "setItem").mockImplementationOnce(() => {
      throw new Error("storage unavailable");
    });
    const persistence = createExpensePersistence(storage);
    persistence.load();

    expect(persistence.startFresh()).toMatchObject({ kind: "error" });
    expect(memory.value).toBe(malformedValue);
    expect(persistence.save([firstExpense])).toEqual({ kind: "blocked" });
  });
});

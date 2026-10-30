import { describe, expect, it } from "vitest";
import { STORAGE_KEY } from "../app/src/content";
import {
  emptyLocalState,
  formatTime,
  loadLocalState,
  remainingSeconds,
} from "../app/src/session";

describe("local session state", () => {
  it("returns an empty state when storage is empty or malformed", () => {
    expect(loadLocalState({ getItem: () => null }).consent).toBe(false);
    expect(
      loadLocalState({ getItem: () => "not-json" }).sessionsCompleted,
    ).toBe(0);
  });

  it("keeps only known goals and valid confidence ratings", () => {
    const state = loadLocalState({
      getItem: () =>
        JSON.stringify({
          consent: true,
          preConfidence: 3,
          postConfidence: 9,
          completedGoalIds: ["opening", "opening", "unknown"],
          sessionsCompleted: 2,
        }),
    });
    expect(state.preConfidence).toBe(3);
    expect(state.postConfidence).toBeNull();
    expect(state.completedGoalIds).toEqual(["opening"]);
  });

  it("uses the intended storage key without media fields", () => {
    expect(STORAGE_KEY).toBe("campus-voices.local.v1");
    expect(emptyLocalState()).not.toHaveProperty("recording");
    expect(emptyLocalState()).not.toHaveProperty("transcript");
  });
});

describe("five-minute timer", () => {
  it("calculates and formats remaining time", () => {
    expect(remainingSeconds(1_000, 61_000)).toBe(240);
    expect(remainingSeconds(1_000, 900_000)).toBe(0);
    expect(formatTime(300)).toBe("05:00");
    expect(formatTime(0)).toBe("00:00");
  });
});

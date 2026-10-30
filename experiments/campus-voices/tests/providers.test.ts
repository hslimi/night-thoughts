import { describe, expect, it, vi } from "vitest";
import { SEMINAR_PROMPTS } from "../app/src/content";
import { DessaVoiceProvider } from "../app/src/providers/dessa-provider";
import { ScriptedVoiceProvider } from "../app/src/providers/scripted-provider";

describe("voice providers", () => {
  it("plays the simulated partner script without media APIs", () => {
    const provider = new ScriptedVoiceProvider();
    const listener = vi.fn();
    provider.onPrompt(listener);
    provider.start();
    provider.nextPrompt();
    expect(listener).toHaveBeenNthCalledWith(1, SEMINAR_PROMPTS[0]);
    expect(listener).toHaveBeenNthCalledWith(2, SEMINAR_PROMPTS[1]);
    provider.stop();
    provider.nextPrompt();
    expect(listener).toHaveBeenCalledTimes(2);
  });

  it("keeps Dessa unavailable when real access is not configured", () => {
    const provider = new DessaVoiceProvider();
    expect(provider.available).toBe(false);
    expect(provider.label).toContain("future provider");
    expect(() => provider.start()).toThrow(/disabled/);
  });
});

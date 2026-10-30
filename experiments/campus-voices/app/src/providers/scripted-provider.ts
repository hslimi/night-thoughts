import { SEMINAR_PROMPTS, type PartnerPrompt } from "../content";
import type { VoiceProvider } from "./voice-provider";

export class ScriptedVoiceProvider implements VoiceProvider {
  readonly id = "scripted" as const;
  readonly label = "Scripted practice provider";
  readonly available = true;

  private promptIndex = 0;
  private listener: ((prompt: PartnerPrompt) => void) | undefined;

  start(): void {
    this.promptIndex = 0;
    this.listener?.(SEMINAR_PROMPTS[this.promptIndex]);
  }

  nextPrompt(): void {
    this.promptIndex = Math.min(
      this.promptIndex + 1,
      SEMINAR_PROMPTS.length - 1,
    );
    this.listener?.(SEMINAR_PROMPTS[this.promptIndex]);
  }

  onPrompt(listener: (prompt: PartnerPrompt) => void): () => void {
    this.listener = listener;
    return () => {
      if (this.listener === listener) this.listener = undefined;
    };
  }

  stop(): void {
    this.listener = undefined;
  }
}

import type { VoiceProvider } from "./voice-provider";

export class DessaVoiceProvider implements VoiceProvider {
  readonly id = "dessa" as const;
  readonly label = "Dessa · future provider";
  readonly available = false;

  start(): void {
    throw new Error(
      "Dessa is disabled because real provider access is not configured.",
    );
  }

  nextPrompt(): void {
    throw new Error(
      "Dessa is disabled because real provider access is not configured.",
    );
  }

  onPrompt(): () => void {
    return () => undefined;
  }

  stop(): void {}
}

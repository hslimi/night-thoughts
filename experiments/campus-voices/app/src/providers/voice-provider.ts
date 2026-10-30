import type { PartnerPrompt } from "../content";

export interface VoiceProvider {
  readonly id: "scripted" | "dessa";
  readonly label: string;
  readonly available: boolean;
  start(): void;
  nextPrompt(): void;
  onPrompt(listener: (prompt: PartnerPrompt) => void): () => void;
  stop(): void;
}

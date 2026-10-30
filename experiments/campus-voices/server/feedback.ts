export interface FeedbackInput {
  preConfidence: number;
  completedGoalIds: string[];
  elapsedSeconds: number;
}

export interface FeedbackResult {
  message: string;
  source: "scripted" | "omlx";
}

export interface OmlxConfig {
  baseUrl?: string;
  model?: string;
  apiKey?: string;
}

export type FeedbackGenerator = (
  input: FeedbackInput,
) => Promise<FeedbackResult>;

const VALID_GOALS = new Set([
  "opening",
  "reasoning",
  "question",
  "build",
  "follow-up",
]);

export function parseFeedbackInput(value: unknown): FeedbackInput | undefined {
  if (!value || typeof value !== "object") return undefined;
  const input = value as Record<string, unknown>;
  if (
    typeof input.preConfidence !== "number" ||
    !Number.isInteger(input.preConfidence) ||
    input.preConfidence < 1 ||
    input.preConfidence > 5 ||
    typeof input.elapsedSeconds !== "number" ||
    !Number.isFinite(input.elapsedSeconds) ||
    input.elapsedSeconds < 0 ||
    input.elapsedSeconds > 300 ||
    !Array.isArray(input.completedGoalIds)
  ) {
    return undefined;
  }

  const completedGoalIds = [...new Set(input.completedGoalIds)];
  if (
    completedGoalIds.length > 5 ||
    completedGoalIds.some(
      (id) => typeof id !== "string" || !VALID_GOALS.has(id),
    )
  ) {
    return undefined;
  }

  return {
    preConfidence: input.preConfidence,
    completedGoalIds,
    elapsedSeconds: Math.round(input.elapsedSeconds),
  };
}

export function scriptedFeedback(input: FeedbackInput): FeedbackResult {
  const count = input.completedGoalIds.length;
  let message: string;

  if (count === 0) {
    message =
      "You gave yourself a quiet place to begin. Showing up for practice is a useful first step; next time, you might try just one opening thought and let it be unfinished.";
  } else if (count < 3) {
    message = `You explored ${count} participation ${count === 1 ? "goal" : "goals"} and made space for your own contribution. Keep the next step small: one idea, one question, or one response is enough.`;
  } else {
    message = `You explored ${count} ways to take part in a seminar conversation. Notice which one felt most possible for you, and carry that small opening into your next practice.`;
  }

  return { message, source: "scripted" };
}

export function createFeedbackGenerator(
  config: OmlxConfig,
  fetchImplementation: typeof fetch = fetch,
): FeedbackGenerator {
  return async (input) => {
    const configured =
      config.baseUrl &&
      config.model &&
      config.apiKey &&
      config.apiKey !== "replace-locally" &&
      config.model !== "replace-with-your-local-model";

    if (!configured) return scriptedFeedback(input);

    try {
      const response = await fetchImplementation(
        `${config.baseUrl?.replace(/\/$/, "")}/chat/completions`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${config.apiKey}`,
          },
          body: JSON.stringify({
            model: config.model,
            temperature: 0.3,
            max_tokens: 140,
            chat_template_kwargs: { enable_thinking: false },
            messages: [
              {
                role: "system",
                content:
                  "Write a 45-65 word supportive note addressed directly to the participant as 'you' after private seminar-speaking practice. Refer only to the supplied metrics. No audio is captured: never say that you heard or listened to the participant, and never suggest recording or transcription. Do not claim progress, improvement, growth, confidence changes, or learning. Do not mention your own feelings or presentations. Support effort without grading. Do not infer accent, emotion, academic ability, or diagnosis. End with one small optional next step. Do not ask for identifying information.",
              },
              {
                role: "user",
                content: JSON.stringify({
                  startingConfidenceOutOfFive: input.preConfidence,
                  selfReportedGoalsExploredOutOfFive:
                    input.completedGoalIds.length,
                  practiceSeconds: input.elapsedSeconds,
                }),
              },
            ],
          }),
          signal: AbortSignal.timeout(60_000),
        },
      );
      if (!response.ok) throw new Error("The local model returned an error.");
      const payload = (await response.json()) as {
        choices?: Array<{ message?: { content?: unknown } }>;
      };
      const content = payload.choices?.[0]?.message?.content;
      if (
        typeof content !== "string" ||
        !content.trim() ||
        !isSafeModelFeedback(content)
      )
        throw new Error("The local model returned unusable feedback.");
      return { message: content.trim(), source: "omlx" };
    } catch {
      return scriptedFeedback(input);
    }
  };
}

export function isSafeModelFeedback(content: string): boolean {
  const unsupportedContent =
    /\b(record(?:ing|ed)?|transcri\w*|heard|listened|listening|progress|improv(?:e|ed|ement)|growth|learning|more confident|significant strides|grade[ds]?|scor(?:e|ed|ing))\b/i;
  return content.length <= 1200 && !unsupportedContent.test(content);
}

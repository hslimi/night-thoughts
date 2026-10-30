import { describe, expect, it, vi } from "vitest";
import {
  createFeedbackGenerator,
  parseFeedbackInput,
  scriptedFeedback,
} from "../server/feedback";

const input = {
  preConfidence: 2,
  completedGoalIds: ["opening", "question"],
  elapsedSeconds: 180,
};

describe("anonymous feedback metrics", () => {
  it("accepts only valid goals and bounded ratings and time", () => {
    expect(parseFeedbackInput(input)).toEqual(input);
    expect(parseFeedbackInput({ ...input, preConfidence: 6 })).toBeUndefined();
    expect(
      parseFeedbackInput({ ...input, completedGoalIds: ["unknown"] }),
    ).toBeUndefined();
    expect(
      parseFeedbackInput({ ...input, elapsedSeconds: 301 }),
    ).toBeUndefined();
  });

  it("returns supportive scripted feedback without a score", () => {
    const result = scriptedFeedback(input);
    expect(result.source).toBe("scripted");
    expect(result.message).toContain("2 participation goals");
    expect(result.message).not.toContain("Dessa");
  });
});

describe("server-side oMLX feedback", () => {
  it("uses the scripted fallback when configuration is incomplete", async () => {
    const fetchMock = vi.fn();
    const generate = createFeedbackGenerator(
      { apiKey: "not-a-real-key" },
      fetchMock,
    );
    const result = await generate(input);
    expect(result.source).toBe("scripted");
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("sends only aggregate metrics to the configured local endpoint", async () => {
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(
        JSON.stringify({
          choices: [
            { message: { content: "You gave your idea room to grow." } },
          ],
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );
    const generate = createFeedbackGenerator(
      {
        baseUrl: "http://localhost:8000/v1",
        model: "local-test-model",
        apiKey: "not-a-real-key",
      },
      fetchMock,
    );
    const result = await generate(input);
    expect(result).toEqual({
      message: "You gave your idea room to grow.",
      source: "omlx",
    });
    const request = fetchMock.mock.calls[0];
    expect(request?.[0]).toBe("http://localhost:8000/v1/chat/completions");
    const body = JSON.parse(String(request?.[1]?.body));
    expect(JSON.parse(body.messages[1].content)).toEqual({
      startingConfidenceOutOfFive: 2,
      selfReportedGoalsExploredOutOfFive: 2,
      practiceSeconds: 180,
    });
  });

  it("falls back without exposing a local model error", async () => {
    const fetchMock = vi
      .fn<typeof fetch>()
      .mockRejectedValue(new Error("offline"));
    const generate = createFeedbackGenerator(
      {
        baseUrl: "http://localhost:8000/v1",
        model: "local-test-model",
        apiKey: "not-a-real-key",
      },
      fetchMock,
    );
    expect((await generate(input)).source).toBe("scripted");
  });

  it("rejects model feedback that conflicts with privacy or measurement limits", async () => {
    const unsafeResponses = [
      "Consider recording your next session.",
      "I heard your voice and noticed progress.",
    ];
    for (const content of unsafeResponses) {
      const fetchMock = vi
        .fn<typeof fetch>()
        .mockResolvedValue(
          new Response(
            JSON.stringify({ choices: [{ message: { content } }] }),
            { status: 200, headers: { "Content-Type": "application/json" } },
          ),
        );
      const generate = createFeedbackGenerator(
        {
          baseUrl: "http://localhost:8000/v1",
          model: "local-test-model",
          apiKey: "not-a-real-key",
        },
        fetchMock,
      );
      expect((await generate(input)).source).toBe("scripted");
    }
  });
});

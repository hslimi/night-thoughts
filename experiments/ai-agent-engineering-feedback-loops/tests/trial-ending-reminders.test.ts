import { describe, expect, it } from "vitest";
import {
  sendTrialEndingReminder,
  type TrialEndingReminderStore,
  type Subscription,
  type TrialEndingReminderEmail,
} from "../src/trial-ending-reminders";

const NOW = new Date("2026-01-10T12:00:00.000Z");
const HOUR_IN_MILLISECONDS = 60 * 60 * 1000;

class InMemoryTrialEndingReminderStore implements TrialEndingReminderStore {
  private readonly recordedSubscriptionIds = new Set<string>();

  constructor(recorded = false) {
    if (recorded) {
      this.recordedSubscriptionIds.add("subscription-1");
    }
  }

  async has(subscriptionId: string): Promise<boolean> {
    return this.recordedSubscriptionIds.has(subscriptionId);
  }

  async record(subscriptionId: string): Promise<void> {
    this.recordedSubscriptionIds.add(subscriptionId);
  }
}

class RecordingEmail implements TrialEndingReminderEmail {
  readonly sentSubscriptions: Subscription[] = [];

  async send(subscription: Subscription): Promise<void> {
    this.sentSubscriptions.push(subscription);
  }
}

function makeSubscription(overrides: Partial<Subscription> = {}): Subscription {
  return {
    id: "subscription-1",
    customerEmail: "customer@example.com",
    status: "trialing",
    trialEndsAt: new Date(NOW.getTime() + 24 * HOUR_IN_MILLISECONDS),
    ...overrides,
  };
}

function makeHarness(subscription: Subscription, recorded = false) {
  const store = new InMemoryTrialEndingReminderStore(recorded);
  const email = new RecordingEmail();
  const send = () =>
    sendTrialEndingReminder(subscription, NOW, store, email);

  return { email, send, store };
}

describe("sendTrialEndingReminder", () => {
  it("sends and records a reminder for an eligible trialing subscription", async () => {
    const { email, send, store } = makeHarness(makeSubscription());

    await expect(send()).resolves.toBe("sent");

    expect(email.sentSubscriptions).toHaveLength(1);
    await expect(store.has("subscription-1")).resolves.toBe(true);
  });

  it("sends when the trial ends exactly 72 hours away", async () => {
    const subscription = makeSubscription({
      trialEndsAt: new Date(NOW.getTime() + 72 * HOUR_IN_MILLISECONDS),
    });
    const { email, send } = makeHarness(subscription);

    await expect(send()).resolves.toBe("sent");
    expect(email.sentSubscriptions).toHaveLength(1);
  });

  it("skips when the trial ends more than 72 hours away", async () => {
    const subscription = makeSubscription({
      trialEndsAt: new Date(
        NOW.getTime() + 72 * HOUR_IN_MILLISECONDS + 1,
      ),
    });
    const { email, send, store } = makeHarness(subscription);

    await expect(send()).resolves.toBe("skipped");
    expect(email.sentSubscriptions).toHaveLength(0);
    await expect(store.has(subscription.id)).resolves.toBe(false);
  });

  it("skips when the trial ends at the current instant", async () => {
    const { email, send } = makeHarness(
      makeSubscription({ trialEndsAt: NOW }),
    );

    await expect(send()).resolves.toBe("skipped");
    expect(email.sentSubscriptions).toHaveLength(0);
  });

  it("skips an expired trial", async () => {
    const { email, send } = makeHarness(
      makeSubscription({
        trialEndsAt: new Date(NOW.getTime() - 1),
      }),
    );

    await expect(send()).resolves.toBe("skipped");
    expect(email.sentSubscriptions).toHaveLength(0);
  });

  it.each(["active", "cancelled"] as const)(
    "skips a %s subscription even inside the eligibility window",
    async (status) => {
      const { email, send } = makeHarness(makeSubscription({ status }));

      await expect(send()).resolves.toBe("skipped");
      expect(email.sentSubscriptions).toHaveLength(0);
    },
  );

  it("skips when a trial-ending reminder is already recorded", async () => {
    const { email, send } = makeHarness(makeSubscription(), true);

    await expect(send()).resolves.toBe("skipped");
    expect(email.sentSubscriptions).toHaveLength(0);
  });

  it("does not send a duplicate when the worker retries", async () => {
    const { email, send } = makeHarness(makeSubscription());

    await expect(send()).resolves.toBe("sent");
    await expect(send()).resolves.toBe("skipped");

    expect(email.sentSubscriptions).toHaveLength(1);
  });

  it("compares ISO offsets as absolute UTC instants", async () => {
    const subscription = makeSubscription({
      trialEndsAt: new Date("2026-01-13T07:00:00.000-05:00"),
    });
    const { email, send } = makeHarness(subscription);

    await expect(send()).resolves.toBe("sent");
    expect(email.sentSubscriptions).toHaveLength(1);
  });
});

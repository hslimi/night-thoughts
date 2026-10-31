export type SubscriptionStatus = "trialing" | "active" | "cancelled";

export interface Subscription {
  id: string;
  customerEmail: string;
  status: SubscriptionStatus;
  trialEndsAt: Date;
}

export interface TrialEndingReminderStore {
  has(subscriptionId: string): Promise<boolean>;
  record(subscriptionId: string): Promise<void>;
}

export interface TrialEndingReminderEmail {
  send(subscription: Subscription): Promise<void>;
}

const REMINDER_WINDOW_IN_MILLISECONDS = 72 * 60 * 60 * 1000;

export async function sendTrialEndingReminder(
  subscription: Subscription,
  now: Date,
  store: TrialEndingReminderStore,
  email: TrialEndingReminderEmail,
): Promise<"sent" | "skipped"> {
  const remaining = subscription.trialEndsAt.getTime() - now.getTime();

  if (
    subscription.status !== "trialing" ||
    remaining <= 0 ||
    remaining > REMINDER_WINDOW_IN_MILLISECONDS ||
    (await store.has(subscription.id))
  ) {
    return "skipped";
  }

  await email.send(subscription);
  await store.record(subscription.id);
  return "sent";
}

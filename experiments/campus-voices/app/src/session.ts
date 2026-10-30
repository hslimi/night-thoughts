import {
  PARTICIPATION_GOALS,
  SESSION_DURATION_SECONDS,
  STORAGE_KEY,
} from "./content";

export interface LocalSessionState {
  version: 1;
  consent: boolean;
  preConfidence: number | null;
  postConfidence: number | null;
  completedGoalIds: string[];
  sessionsCompleted: number;
  updatedAt: string;
}

export const emptyLocalState = (): LocalSessionState => ({
  version: 1,
  consent: false,
  preConfidence: null,
  postConfidence: null,
  completedGoalIds: [],
  sessionsCompleted: 0,
  updatedAt: new Date().toISOString(),
});

export function loadLocalState(
  storage: Pick<Storage, "getItem">,
): LocalSessionState {
  const raw = storage.getItem(STORAGE_KEY);
  if (!raw) return emptyLocalState();

  try {
    const value = JSON.parse(raw) as Partial<LocalSessionState>;
    const validGoals = Array.isArray(value.completedGoalIds)
      ? value.completedGoalIds.filter((id): id is string =>
          PARTICIPATION_GOALS.some((goal) => goal.id === id),
        )
      : [];

    return {
      ...emptyLocalState(),
      consent: value.consent === true,
      preConfidence: isConfidence(value.preConfidence)
        ? value.preConfidence
        : null,
      postConfidence: isConfidence(value.postConfidence)
        ? value.postConfidence
        : null,
      completedGoalIds: [...new Set(validGoals)],
      sessionsCompleted:
        typeof value.sessionsCompleted === "number" &&
        value.sessionsCompleted >= 0
          ? Math.floor(value.sessionsCompleted)
          : 0,
      updatedAt:
        typeof value.updatedAt === "string"
          ? value.updatedAt
          : new Date().toISOString(),
    };
  } catch {
    return emptyLocalState();
  }
}

export function remainingSeconds(startedAt: number, now: number): number {
  return Math.max(
    0,
    SESSION_DURATION_SECONDS - Math.floor((now - startedAt) / 1000),
  );
}

export function formatTime(totalSeconds: number): string {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

function isConfidence(value: unknown): value is number {
  return (
    typeof value === "number" &&
    Number.isInteger(value) &&
    value >= 1 &&
    value <= 5
  );
}

import "./styles.css";
import {
  PARTICIPATION_GOALS,
  SESSION_DURATION_SECONDS,
  STORAGE_KEY,
  type PartnerPrompt,
} from "./content";
import { ScriptedVoiceProvider } from "./providers/scripted-provider";
import {
  emptyLocalState,
  formatTime,
  loadLocalState,
  remainingSeconds,
} from "./session";

type Screen = "welcome" | "session" | "feedback";

interface Feedback {
  message: string;
  source: "scripted" | "omlx";
}

const app = document.querySelector<HTMLDivElement>("#app") as HTMLDivElement;

let screen: Screen = "welcome";
let localState = loadLocalState(window.localStorage);
let consent = localState.consent;
let preConfidence = localState.preConfidence;
let startedAt = 0;
let practiceSeconds = 0;
let prompts: PartnerPrompt[] = [];
let provider: ScriptedVoiceProvider | undefined;
let timer: ReturnType<typeof setInterval> | undefined;
let feedback: Feedback | undefined;
let notice = "";

function saveLocalState(): void {
  localState.updatedAt = new Date().toISOString();
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(localState));
}

function header(): string {
  return `
    <header class="site-header">
      <a class="brand" href="/" aria-label="Campus Voices home">
        <span class="brand-mark" aria-hidden="true"><span></span><span></span><span></span></span>
        <span><strong>Campus Voices</strong><small>A Night Thoughts experiment</small></span>
      </a>
      <button class="text-button" data-open-privacy>Privacy &amp; local data</button>
    </header>`;
}

function privacyDialog(): string {
  return `
    <dialog id="privacy-dialog" class="privacy-dialog" aria-labelledby="privacy-title">
      <div class="dialog-kicker">YOUR DATA, YOUR DEVICE</div>
      <h2 id="privacy-title">Practice without leaving a voice trail.</h2>
      <p>This scripted prototype does not request microphone access and creates no recordings or transcripts.</p>
      <dl class="privacy-list">
        <div><dt>Stored in this browser</dt><dd>Consent, confidence ratings, goal check-offs, and a session count.</dd></div>
        <div><dt>Sent to the app server</dt><dd>Only anonymous practice metrics when requesting supportive feedback.</dd></div>
        <div><dt>Never collected</dt><dd>Names, student records, audio, transcripts, accent scores, or emotion inference.</dd></div>
      </dl>
      <p class="storage-note">Storage key: <code>${STORAGE_KEY}</code></p>
      <div class="dialog-actions">
        <button class="button button-danger" data-delete-local>Delete local data</button>
        <button class="button button-secondary" data-close-privacy>Keep practising</button>
      </div>
    </dialog>`;
}

function footer(): string {
  return `<footer class="site-footer"><span>Private by design. Supportive by default.</span><span>Scripted prototype · Not a student study</span></footer>`;
}

function renderWelcome(): string {
  return `
    <main>
      <section class="hero">
        <div class="hero-copy">
          <div class="eyebrow"><span class="status-dot"></span> PRIVATE SPEAKING LAB · SYNTHETIC DEMO</div>
          <h1>Find your voice<br />before the seminar begins.</h1>
          <p class="hero-intro">A quiet space to practise contributing, asking questions, and building on ideas—without being recorded, graded, or analysed.</p>
          <div class="trust-row" aria-label="Privacy properties">
            <span>No recording</span><span>No transcript</span><span>Local-only progress</span>
          </div>
        </div>
        <aside class="scenario-card">
          <div class="card-topline"><span>PRACTICE SCENARIO 01</span><span class="duration-pill">5 MINUTES</span></div>
          <h2>My First Seminar<br />Contribution</h2>
          <p>Join Sam, a simulated seminar partner, and rehearse one small contribution at your own pace.</p>
          <div class="provider-row"><span class="provider-icon">S</span><div><strong>Scripted practice provider</strong><small>Dessa is a disabled future provider</small></div></div>
        </aside>
      </section>

      <section class="setup-grid">
        <div class="setup-step consent-step">
          <span class="step-number">01</span>
          <div><h3>Choose private practice</h3><p>No account. No student data. Just this browser.</p></div>
          <label class="consent-label">
            <input type="checkbox" data-consent ${consent ? "checked" : ""} />
            <span>I understand this is a synthetic prototype and consent to store my practice choices on this device.</span>
          </label>
        </div>
        <div class="setup-step confidence-step">
          <span class="step-number">02</span>
          <div><h3>How confident do you feel?</h3><p>A private check-in, not an assessment.</p></div>
          <div class="confidence-control" aria-label="Pre-session confidence from one to five">
            ${confidenceButtons(preConfidence, "pre")}
          </div>
          <div class="confidence-labels"><span>Not yet</span><span>Ready to try</span></div>
        </div>
        <div class="begin-panel">
          <button class="button button-primary" data-start ${!consent || !preConfidence ? "disabled" : ""}>Begin private practice <span aria-hidden="true">→</span></button>
          <small>You can end the session at any time.</small>
        </div>
      </section>

      <section class="goals-section" aria-labelledby="goals-title">
        <div class="section-heading"><div><div class="eyebrow">FIVE SMALL WAYS IN</div><h2 id="goals-title">Participation is more than one perfect answer.</h2></div><p>Choose any goals that feel useful. There is no score and no required order.</p></div>
        <div class="goal-grid">
          ${PARTICIPATION_GOALS.map(
            (goal, index) =>
              `<article class="goal-card"><span>${String(index + 1).padStart(2, "0")}</span><h3>${goal.title}</h3><p>${goal.description}</p></article>`,
          ).join("")}
        </div>
      </section>
    </main>`;
}

function renderSession(): string {
  return `
    <main class="session-main">
      <section class="session-heading">
        <div><div class="eyebrow"><span class="status-dot"></span> MY FIRST SEMINAR CONTRIBUTION</div><h1>Your turn to take up a little space.</h1><p>Speak aloud naturally. Sam’s prompts are scripted; your voice is not captured.</p></div>
        <div class="timer-card"><small>PRACTICE TIME</small><strong data-timer>${formatTime(remainingSeconds(startedAt, Date.now()))}</strong><div class="timer-track"><span data-timer-progress></span></div></div>
      </section>
      <section class="practice-grid">
        <article class="partner-panel">
          <div class="panel-header"><div class="partner-identity"><span class="partner-avatar">S</span><div><strong>Sam</strong><small>Simulated seminar partner</small></div></div><span class="local-badge">SCRIPTED · NO AUDIO</span></div>
          <div class="prompt-list" data-prompt-list aria-live="polite">${promptMarkup()}</div>
          <div class="speaking-cue"><span class="speaking-lines" aria-hidden="true"><i></i><i></i><i></i><i></i></span><div><strong>Speak at your own pace</strong><small>Only your button choices are saved.</small></div></div>
          <button class="button button-secondary next-prompt" data-next-prompt>Next partner prompt <span aria-hidden="true">→</span></button>
        </article>
        <aside class="session-goals">
          <div class="panel-header"><div><div class="eyebrow">YOUR PRACTICE GOALS</div><h2><span data-goal-count>${localState.completedGoalIds.length}</span> of 5 explored</h2></div></div>
          <p class="goal-help">Mark a goal when you have tried it. This is self-reflection, not grading.</p>
          <div class="session-goal-list">
            ${PARTICIPATION_GOALS.map((goal) => {
              const complete = localState.completedGoalIds.includes(goal.id);
              return `<button class="session-goal ${complete ? "complete" : ""}" data-goal="${goal.id}" aria-pressed="${complete}"><span class="goal-check">${complete ? "✓" : ""}</span><span><strong>${goal.title}</strong><small>${complete ? "Explored in this session" : "Mark when you have tried this"}</small></span></button>`;
            }).join("")}
          </div>
          <button class="button button-end" data-end-session>End session <span aria-hidden="true">→</span></button>
          <p class="end-note">You are in control. Ending early still counts as practice.</p>
        </aside>
      </section>
    </main>`;
}

function renderFeedback(): string {
  if (!feedback) {
    return `<main class="feedback-main"><section class="feedback-card loading-card"><div class="eyebrow">PRIVATE REFLECTION</div><h1>Gathering your supportive feedback…</h1><p>No recording or transcript is being analysed.</p></section></main>`;
  }

  return `
    <main class="feedback-main">
      <section class="feedback-heading"><div class="completion-mark" aria-hidden="true">✓</div><div class="eyebrow">SESSION COMPLETE · SYNTHETIC DEMONSTRATION</div><h1>You made room for your voice.</h1><p>Practice is not about becoming a different speaker. It is about finding a way in that feels possible for you.</p></section>
      <section class="feedback-layout">
        <article class="feedback-card">
          <div class="card-topline"><span>A NOTE AFTER YOUR PRACTICE</span><span class="feedback-source">${feedback.source === "omlx" ? "LOCAL oMLX" : "SCRIPTED PROTOTYPE"}</span></div>
          <blockquote>${escapeHtml(feedback.message)}</blockquote>
          <div class="feedback-metrics"><div><strong>${localState.completedGoalIds.length}<span>/5</span></strong><small>goals explored</small></div><div><strong>${formatTime(practiceSeconds)}</strong><small>practice time</small></div><div><strong>${preConfidence}<span>/5</span></strong><small>starting confidence</small></div></div>
          <p class="feedback-disclaimer">Supportive reflection only. No accent, emotion, academic ability, or learning outcome has been measured.</p>
        </article>
        <aside class="post-card">
          <div class="eyebrow">ONE LAST PRIVATE CHECK-IN</div><h2>How confident do you feel now?</h2><p>Any answer is okay. This is your reflection, not a result.</p>
          <div class="confidence-control post-confidence" aria-label="Post-session confidence from one to five">${confidenceButtons(localState.postConfidence, "post")}</div>
          <div class="confidence-labels"><span>Not yet</span><span>Ready to try</span></div>
          <div class="post-actions"><button class="button button-primary" data-practice-again>Practice again <span aria-hidden="true">↻</span></button><button class="text-button delete-link" data-delete-local>Delete local data</button></div>
        </aside>
      </section>
      <section class="reflection-strip"><strong>What stays here?</strong><span>Your choices remain in this browser until you delete them. No voice or text recording was created.</span><button class="text-button" data-open-privacy>Review privacy controls →</button></section>
    </main>`;
}

function confidenceButtons(
  selected: number | null,
  kind: "pre" | "post",
): string {
  return [1, 2, 3, 4, 5]
    .map(
      (value) =>
        `<button class="confidence-button ${selected === value ? "selected" : ""}" data-${kind}-confidence="${value}" aria-pressed="${selected === value}" aria-label="${kind === "pre" ? "Pre-session" : "Post-session"} confidence ${value} out of 5">${value}</button>`,
    )
    .join("");
}

function promptMarkup(): string {
  return prompts
    .map(
      (prompt, index) =>
        `<div class="prompt ${index === prompts.length - 1 ? "latest" : ""}"><small>${prompt.speaker}</small><p>${prompt.text}</p></div>`,
    )
    .join("");
}

function render(): void {
  if (timer) clearInterval(timer);
  const content =
    screen === "welcome"
      ? renderWelcome()
      : screen === "session"
        ? renderSession()
        : renderFeedback();
  app.innerHTML = `${header()}${content}${footer()}${privacyDialog()}${notice ? `<div class="toast" role="status">${notice}</div>` : ""}`;
  bindCommonActions();

  if (screen === "welcome") bindWelcomeActions();
  if (screen === "session") bindSessionActions();
  if (screen === "feedback") bindFeedbackActions();
}

function bindCommonActions(): void {
  const dialog = document.querySelector<HTMLDialogElement>("#privacy-dialog");
  document
    .querySelectorAll("[data-open-privacy]")
    .forEach((button) =>
      button.addEventListener("click", () => dialog?.showModal()),
    );
  document
    .querySelector("[data-close-privacy]")
    ?.addEventListener("click", () => dialog?.close());
  dialog?.addEventListener("click", (event) => {
    if (event.target === dialog) dialog.close();
  });
  document
    .querySelectorAll("[data-delete-local]")
    .forEach((button) => button.addEventListener("click", deleteLocalData));
}

function bindWelcomeActions(): void {
  document
    .querySelector<HTMLInputElement>("[data-consent]")
    ?.addEventListener("change", (event) => {
      consent = (event.target as HTMLInputElement).checked;
      localState.consent = consent;
      saveLocalState();
      render();
    });
  document
    .querySelectorAll<HTMLButtonElement>("[data-pre-confidence]")
    .forEach((button) => {
      button.addEventListener("click", () => {
        preConfidence = Number(button.dataset.preConfidence);
        localState.preConfidence = preConfidence;
        localState.postConfidence = null;
        saveLocalState();
        render();
      });
    });
  document
    .querySelector("[data-start]")
    ?.addEventListener("click", startSession);
}

function bindSessionActions(): void {
  document
    .querySelector("[data-next-prompt]")
    ?.addEventListener("click", () => provider?.nextPrompt());
  document
    .querySelectorAll<HTMLButtonElement>("[data-goal]")
    .forEach((button) => {
      button.addEventListener("click", () => {
        const id = button.dataset.goal;
        if (!id) return;
        localState.completedGoalIds = localState.completedGoalIds.includes(id)
          ? localState.completedGoalIds.filter((goalId) => goalId !== id)
          : [...localState.completedGoalIds, id];
        saveLocalState();
        render();
      });
    });
  document
    .querySelector("[data-end-session]")
    ?.addEventListener("click", finishSession);
  updateTimer();
  timer = setInterval(updateTimer, 250);
}

function bindFeedbackActions(): void {
  document
    .querySelectorAll<HTMLButtonElement>("[data-post-confidence]")
    .forEach((button) => {
      button.addEventListener("click", () => {
        localState.postConfidence = Number(button.dataset.postConfidence);
        saveLocalState();
        render();
      });
    });
  document
    .querySelector("[data-practice-again]")
    ?.addEventListener("click", () => {
      localState = {
        ...emptyLocalState(),
        consent,
        sessionsCompleted: localState.sessionsCompleted,
      };
      preConfidence = null;
      feedback = undefined;
      screen = "welcome";
      saveLocalState();
      render();
    });
}

function startSession(): void {
  if (!consent || !preConfidence) return;
  notice = "";
  prompts = [];
  feedback = undefined;
  startedAt = Date.now();
  localState.preConfidence = preConfidence;
  localState.postConfidence = null;
  localState.completedGoalIds = [];
  saveLocalState();
  provider = new ScriptedVoiceProvider();
  provider.onPrompt((prompt) => {
    prompts.push(prompt);
    const list = document.querySelector<HTMLElement>("[data-prompt-list]");
    if (list) {
      list.innerHTML = promptMarkup();
      list.scrollTop = list.scrollHeight;
    }
  });
  screen = "session";
  render();
  provider.start();
}

function updateTimer(): void {
  const remaining = remainingSeconds(startedAt, Date.now());
  const timerElement = document.querySelector<HTMLElement>("[data-timer]");
  const progress = document.querySelector<HTMLElement>("[data-timer-progress]");
  if (timerElement) timerElement.textContent = formatTime(remaining);
  if (progress)
    progress.style.width = `${(remaining / SESSION_DURATION_SECONDS) * 100}%`;
  if (remaining === 0 && screen === "session") void finishSession();
}

async function finishSession(): Promise<void> {
  if (screen !== "session") return;
  practiceSeconds = Math.min(
    SESSION_DURATION_SECONDS,
    Math.max(1, Math.round((Date.now() - startedAt) / 1000)),
  );
  provider?.stop();
  if (timer) clearInterval(timer);
  localState.sessionsCompleted += 1;
  saveLocalState();
  feedback = undefined;
  screen = "feedback";
  render();

  try {
    const response = await window.fetch("/api/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        preConfidence,
        completedGoalIds: localState.completedGoalIds,
        elapsedSeconds: practiceSeconds,
      }),
    });
    if (!response.ok) throw new Error("Feedback request failed.");
    feedback = (await response.json()) as Feedback;
  } catch {
    feedback = {
      source: "scripted",
      message:
        "You showed up and gave yourself time to practise. That is worthwhile in itself. Next time, you might choose just one small goal and see how it feels.",
    };
  }
  render();
}

function deleteLocalData(): void {
  window.localStorage.removeItem(STORAGE_KEY);
  provider?.stop();
  localState = emptyLocalState();
  consent = false;
  preConfidence = null;
  feedback = undefined;
  prompts = [];
  screen = "welcome";
  notice = "Local practice data deleted from this browser.";
  render();
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>'"]/g, (character) => {
    const entities: Record<string, string> = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      "'": "&#39;",
      '"': "&quot;",
    };
    return entities[character];
  });
}

render();

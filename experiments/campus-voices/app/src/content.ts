export const SESSION_DURATION_SECONDS = 5 * 60;
export const STORAGE_KEY = "campus-voices.local.v1";

export interface ParticipationGoal {
  id: string;
  title: string;
  description: string;
}

export const PARTICIPATION_GOALS: ParticipationGoal[] = [
  {
    id: "opening",
    title: "Make an opening contribution",
    description: "Share one initial thought, even if it is still taking shape.",
  },
  {
    id: "reasoning",
    title: "Explain your reasoning",
    description: "Add a because, an example, or a connection to the reading.",
  },
  {
    id: "question",
    title: "Ask a clarifying question",
    description:
      "Check an idea or invite the group to unpack a difficult point.",
  },
  {
    id: "build",
    title: "Build on a peer’s idea",
    description: "Extend, complicate, or connect to something Sam has said.",
  },
  {
    id: "follow-up",
    title: "Respond to a follow-up",
    description: "Stay with your idea for one more turn and answer a question.",
  },
];

export interface PartnerPrompt {
  id: string;
  speaker: string;
  text: string;
}

export const SEMINAR_PROMPTS: PartnerPrompt[] = [
  {
    id: "welcome",
    speaker: "Sam · simulated seminar partner",
    text: "I’m glad you’re here. What is one idea from this week’s reading that stayed with you? Take your time and speak aloud when you’re ready.",
  },
  {
    id: "reasoning",
    speaker: "Sam · simulated seminar partner",
    text: "That gives us a place to start. What makes that idea important to you? You could add an example or explain your reasoning.",
  },
  {
    id: "question",
    speaker: "Sam · simulated seminar partner",
    text: "I connected that with the author’s argument about belonging. Is there a part you would like to question or clarify?",
  },
  {
    id: "build",
    speaker: "Sam · simulated seminar partner",
    text: "I think participation can feel risky when everyone expects a polished answer. Would you agree, or would you add a different perspective?",
  },
  {
    id: "follow-up",
    speaker: "Sam · simulated seminar partner",
    text: "One follow-up: if you shared that thought in a real seminar, what would you want the group to understand?",
  },
  {
    id: "closing",
    speaker: "Sam · simulated seminar partner",
    text: "You have explored several ways into the conversation. You can keep practising, finish a goal, or end the session whenever you choose.",
  },
];

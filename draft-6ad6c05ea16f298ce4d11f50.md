---
title: "Augmenting, Not Replacing: A Teacher-Supervised Multi-Agent Architecture for Customized Learning with Privacy-by-Design"

---

## Abstract

Adaptive learning platforms have revived an old aspiration: to approximate, at scale, the individualized support that human tutoring provides. Yet the evidence on AI-driven customization is more conditional than the headline promise suggests. This article specifies a design architecture and evaluation protocol for a university course in which a multi-agent system generates weekly psycho-technical questionnaires, scores student profiles, produces calibrated supplementary exercises, corrects submissions, and updates a longitudinal learner model. The design rests on four pillars, presented in the order of the argument. **Customization** is the pedagogical goal, anchored in Bloom's two-sigma benchmark [1], the human–AI complementarity evidence [5], and constructive alignment [11]. **Meaningful human control** is the authority structure, specified through the tracking and tracing criteria [16] and mapped against EU AI Act oversight requirements [17]. **Multi-agent design** is the mechanism. **Privacy-by-design** is the condition, including a right to refuse profiling without academic penalty. The contributions are sixfold: anchoring customization in benchmark evidence and alignment theory rather than in the assumption that personalization is beneficial; specifying human control through tracking and tracing and mapping it against a regulatory checklist; specifying a two-layer decision engine with every rule annotated by epistemic status; specifying a deterministic orchestrator whose exclusive write authority over the audit log is the mechanism by which tracing is preserved; introducing the common supervised probe as a non-circular evaluation instrument; and providing a pre-registered, falsifiable design with an oversight-intensity arm. Across all four pillars, the teacher remains the accountable pedagogical agent.

---

## 1. Introduction

Bloom's 1984 essay, "The 2 Sigma Problem," reported that students taught one-to-one outperformed conventional group instruction by roughly two standard deviations [1]. The finding established both the upper bound of personalized teaching and a structural problem: one-to-one human tutoring is the most effective instructional arrangement documented, and it is economically impossible at scale. Contemporary AI-driven customization is the latest attempt to answer Bloom's question. The results are neither triumphant nor dismissive. Intelligent tutoring systems (ITS) produce gains over teacher-led large-group instruction (*g* = .42) [2], with no significant difference from individualized human tutoring (*g* = –.11) [2,3], but estimates against the most demanding comparators are much smaller: 0.125 standard deviations for adaptive and AI-enabled interventions in the World Bank's meta-analysis of randomized trials, and 0.12 for AI-powered tutoring [4]. The benchmark remains an aspiration.

The evidence also points toward a specific conclusion about the teacher. A field study in real classrooms found that students learned more when teachers and AI tutors worked together than when either operated alone, and its authors argue for designing around **human–AI complementarity** rather than maximizing automation [5]. Teachers themselves identify AI as a complement to assessment and personalization while insisting that emotional, ethical, and contextual roles remain human. The question is therefore not whether AI replaces the teacher, but which parts of teaching can be extended at scale without displacing the teacher's judgment.

This article specifies such an arrangement. **Customization** is the pedagogical objective: weekly cycles of questionnaire, exercise, correction, and recalibration designed to approximate the frequency and granularity of one-to-one support, anchored in an explicit theory of instructional alignment [11,12]. **Meaningful human control** is the authority structure: who is accountable, on what basis, and whether the human presence is substantive or decorative. **Multi-agent architecture** is the mechanism. **Privacy-by-design** is the condition that makes persistent psycho-technical profiling proportionate, contestable, refusable, and trustworthy. The six contributions stated in the Abstract are developed in Sections 2 through 6 and are not re-enumerated here.

---

## 2. Pillar 1 — Customization: Extending the One-to-One Benchmark

### 2.1 The benchmark, the evidence, and the replication record

Bloom's finding is often cited as evidence that personalized instruction is powerful. It is equally important as evidence that the effect was produced by **human tutors** who interpreted confusion, adjusted explanations, motivated persistence, and connected new material to prior knowledge in ways current AI does not replicate [1]. The benchmark carries two implications at once: customization matters enormously, and its human elements are not automatically reproduced by adaptive software.

The empirical record is best read by comparator rather than in sequence. Against conventional group instruction, ITS meta-analyses report *g* = .42 [2]; against the same comparator, AI-driven adaptive learning platforms report Hedges' *g* = 0.276 across 27 studies [6]; and against the same comparator, the World Bank's meta-analysis of randomized trials estimates 0.125 standard deviations for adaptive and AI-enabled interventions overall, with 0.12 for AI-powered tutoring [4]. Against one-to-one human tutoring, meta-analytic comparisons report differences close to zero, with intervals spanning zero in both cases [2,3]. Evidence from large personalized-learning RCTs has been mixed, with modest and uneven effects across sites [7]. The comparators are not interchangeable, the populations differ, and the estimates are not additive.

The replication record of the two-sigma figure itself warrants caution: later analyses cluster nearer 0.8 standard deviations, and the original estimate rested on small samples with mastery learning bundled into the tutoring condition [1,3]. We treat two sigma as a **design target and structural argument** — the reason human tutoring is the reference — rather than as a benchmark any implementation, including ours, is expected to reach.

![Figure A: Effect sizes separated by comparator](https://cdn.hashnode.com/uploads/gql/6a92730f9a9aa7f72e74fdf4/8db2752a-4b1b-4c56-b592-527b8b7c0347.png)

**Figure A. Effect sizes reported in the literature, separated by comparator.** Left panel: effects against conventional group instruction. The hollow bar is Bloom's two-sigma [1], shown as a design aspiration rather than a replicated estimate; later analyses cluster nearer 0.8 SD [3]. Right panel: the single displayed estimate against one-to-one human tutoring [3], reported as non-significant; a comparable near-zero difference is also reported in [2]. No confidence interval is drawn because none is reported in the form we would quote in [3]; the source reports the difference as non-significant rather than an interval, and we state this rather than reconstruct an interval we cannot source. The panels are not additive — they share neither comparator, population, nor technology — and the visual separation is deliberate: co-citation of the two estimates is not a trend claim. Right-hand axis translates effect sizes into approximate percentiles of the median student, assuming normality. Sources: [1,2,3,4,6]. Supplementary Table S3 gives exact values and source notes.

The conclusion is not that customization has failed but that **its design determines whether it approaches or falls short of the benchmark**. The question becomes which components of tutoring can be extended through AI and which must remain with the teacher.

### 2.2 Complementarity as the design principle

The strongest evidence for the teacher's continued role comes from field research on human–AI partnerships. Holstein and Aleven found that students learned more when teachers and AI tutors worked together during class, and they argue for designing around complementary strengths rather than automating the teacher away [5]. Their framework treats the teacher not as a fallback for AI failure but as a source of cognitive and motivational support AI does not provide: encouragement, clarification of misconceptions, connection of new tasks to prior topics. Survey evidence from higher education points the same way. AI is strong at high-frequency, rule-governed, data-intensive tasks. Teachers are strong at interpretation, relational judgment, and contextual adaptation.

Complementarity is not automatic. Human–AI teaming fails in documented ways: algorithm aversion leads people to under-use accurate advice, automation bias to over-trust inaccurate advice, and forced deliberation can attenuate both [8]. The strongest complementarity evidence comes from K-12 classroom orchestration with a specific ITS [9], not from university lecture-and-tutorial structures; its transfer is plausible but is itself a claim. The architecture makes complementarity testable rather than assumed, and the evaluation treats it as a research question.

### 2.3 Why customization is needed, not merely possible

The case for AI customization does not rest on the claim that it outperforms teachers. It rests on three structural constraints. **Frequency**: desirable difficulty and formative feedback require calibration at the level of individual tasks and weeks, not once per term, and sustaining that across a large cohort exceeds human capacity. **Granularity**: psycho-technical profiling requires repeated administration and scoring of multiple instruments with longitudinal updating, beyond human working memory and available time. **Consistency**: without a structured system, customization is applied unevenly, and students who most need calibration are least able to demand it.

These constraints are plausible rather than proven, and the "necessary" claim requires a cost-feasibility comparison against non-AI alternatives. A full ingredients-method analysis [10] is beyond the scope of a protocol paper, but the comparison can be stated at a first approximation. A weekly per-student calibration cycle covering five knowledge components with psycho-technical instruments requires roughly 20–30 minutes of skilled instructional time per student per week. At a tutorial teacher-to-student ratio of 1:50, that is roughly 17–25 additional instructional hours per week per section, plus instrumentation and analysis time. Peer tutoring at a 1:5 ratio delivers documented effects in the 0.3–0.4 standard deviation range, but it implies ten times as many tutors per student as a 1:50 tutorial arrangement. Whether that is more or less expensive per student depends on the wage differential between peer tutors and tutorial teachers, which is large and which we do not assume. The pilot's cost data, collected under the ingredients method [10], will determine whether the AI-mediated arrangement is cheaper per unit of effect than either a smaller-section or a peer-tutoring alternative; the trial is designed to produce that comparison rather than assume its outcome.

### 2.4 Instructional alignment: what the customization is customizing

Adaptive systems are frequently specified in terms of difficulty, feedback, and pace without an explicit account of what the learning objectives are and how items map onto them. This is a design gap, not a stylistic one: if the item bank is not aligned to specified objectives, difficulty calibration optimizes for an undefined construct.

We adopt **constructive alignment** [11]: intended learning outcomes are specified first, assessment tasks are designed to require the verbs those outcomes name, and instructional activities are selected to prepare students for those tasks. The knowledge components used by the decision engine are derived from the intended learning outcomes rather than from the structure of the textbook or lecture sequence. We further adopt the **Knowledge–Learning–Instruction (KLI) framework** [12] as the bridge between learning-science mechanisms and instructional design: the exercise generator is constrained to target identified knowledge components at identified depths, and the correction agent diagnoses errors at the component level rather than assigning holistic scores.

Three mechanisms inform the decision rules in Section 6.3: **desirable difficulty** [13], motivating the target success band; **cognitive load and prior knowledge** [14], motivating prerequisite remediation; and **expertise reversal** [15], motivating reduced guidance as mastery rises. These mechanisms motivate the rules rather than warrant specific parameterizations, and Section 6.3.5 annotates each accordingly. The alignment requirement also has an integrity function: the pedagogical non-regression test in Section 3.6 is only meaningful if there is a specification against which to test.

### 2.5 Division of labor and the floor-raising argument

Table 1 specifies which customization functions are AI-appropriate and which are teacher-reserved. The teacher's role is not reduced but **reconcentrated** on higher-order pedagogical acts.

**Table 1. Division of labor between AI agents and the teacher**

| Function | Primary responsibility | Rationale |
|---|---|---|
| Questionnaire generation at scale | AI | High-frequency, template-driven, data-intensive |
| Psycho-technical scoring | AI, with human review of outliers | Multi-instrument pattern detection |
| Exercise calibration by difficulty | AI | Rule-governed adjustment |
| First-pass correction and feedback | AI, sampled by human | Volume exceeds human capacity |
| Interpretation of anomalous profiles | **Teacher** | Contextual and relational knowledge |
| Escalation decisions | **Teacher** | Accountability cannot be delegated |
| Pedagogical adaptation | **Teacher** | The core professional act of teaching |
| Revision of decision rules | **Teacher**, informed by analytics | Normative judgment about appropriate support |

The equity argument for customization is not that it raises the ceiling for strong students but that it raises the floor for weak ones. Prerequisite remediation targets students below the threshold at which new content becomes productive [14]. The protective ceiling and escalation rule is a safeguarding rule whose beneficiaries are disproportionately students who would otherwise fail silently. The frequency argument applies with most force to students who cannot self-regulate. The cost of *not* calibrating falls disproportionately on students without compensatory resources—private tutoring, family support, prior preparation—and a student who cannot afford external help is the one for whom the weekly feedback cycle substitutes. This motivates the pre-specified subgroup analysis in Section 6.3.8.

The equity claim carries a statistical caution. At the sample size proposed, a positive effect for low-prior-knowledge students may coexist with a null average effect, because gains for weak students are diluted by ceiling effects among strong ones. The design treats the subgroup analysis as exploratory and the average effect as confirmatory; a positive subgroup result in the absence of a main effect narrows the claim rather than rescuing it.

![Figure B: Positioning of the proposed architecture relative to reference systems](https://cdn.hashnode.com/uploads/gql/6a92730f9a9aa7f72e74fdf4/5c92bba0-6f76-422d-8a53-0ee3d85beff1.png)

**Figure B. Positioning of the proposed architecture relative to reference systems, as a qualitative judgement.** Horizontal axis: granularity of pedagogical decision, from single-step item selection to weekly cycle calibration. Vertical axis: locus of pedagogical authority, operationalized as who holds rule-revision authority and who can reverse a decision (see Sections 3.2 and 3.6). The shaded region marks the quadrant for which no AI effect-size evidence exists at this granularity. It denotes an absence of evidence, not an absence of practice: a non-AI course design with weekly formative assessment and teacher-set rules already occupies this quadrant, and a reference point for that design is shown. Positions are qualitative judgements, not measurements. The figure's purpose is to prevent the reader from assuming that the meta-analytic estimates cited in Section 2.1 transfer to the present design.

---

## 3. Pillar 2 — Meaningful Human Control

### 3.1 Why this is a separate pillar

The first pillar answers *why* customization matters, the third *how* it is implemented, the fourth *under what conditions* it is permissible. None answers **who is accountable, on what basis, and whether the human presence is substantive or decorative**. The paper's title makes a claim about human control, and a claim of that kind requires its own evidence base, its own specification, and its own evaluation.

"Human in the loop" has become a phrase satisfiable by a rubber stamp. If a teacher clicks approve on a hundred generated exercises in an hour, a human was present at every decision and control was exercised at none of them. We therefore treat meaningful human control as a design property to be specified, operationalized, and tested.

### 3.2 Tracking and tracing

We adopt Santoni de Sio and van den Hoven's two-criterion specification [16]. **Tracking** requires that the system's actions track the human's reasons and intentions—not merely that a human is aware of what the system is doing, but that its behaviour is responsive to the considerations the human would endorse if asked. In this architecture, tracking is implemented through the decision rules in Section 6.3.5. The teacher approves the rules, can revise them, and the rules encode the teacher's pedagogical reasons rather than an opaque model's preferences. When the teacher overrides a rule for an individual student, the override is logged with a stated reason and the rule's subsequent behaviour for that student reflects it.

**Tracing** requires that an outcome be traceable to a specific human who had the authority and the opportunity to act differently. This is implemented through the audit log (Section 3.6), which records what the agent decided, what the human approved, and what information was available at the time of approval. A grade, an escalation, or an exercise assignment can therefore be attributed to a named human decision rather than to the system as a whole. The audit log is written exclusively by the deterministic orchestrator (Section 4.1) rather than by any agent, so that the component whose decision is recorded cannot also edit the record.

These criteria convert a soft claim into a testable one. Section 6.4 specifies a tracking-and-tracing audit in which an independent rater assesses, for a sample of decisions, whether the system's recommendation reflected the teacher's stated reasons and whether the outcome can be traced to an identifiable human decision.

### 3.3 Regulatory anchor

Education is classified as a high-risk application domain under Annex III of the EU AI Act, and Article 14 specifies human-oversight requirements for high-risk systems: oversight must enable the overseer to understand the system's capacities and limitations, remain aware of automation bias, correctly interpret output, decide not to use the system or to disregard its output, and intervene in or stop its operation [17]. We use Article 14 as a design checklist rather than a compliance claim, since the architecture is described jurisdiction-neutrally. Each requirement maps onto an architectural mechanism: understanding limitations is addressed by the failure-mode taxonomy (Section 4.4) and the epistemic-status annotations (Section 6.3.5); automation-bias awareness by triage-driven escalation and the decision-quality and tracking audits (Sections 3.5 and 6.4); correct interpretation by rule annotations and by restricting escalation notices to actionable signals (Sections 6.3.5 and 5.4); the decision to disregard by teacher override with logged reason and propagation to the student's rule behaviour (Sections 3.2 and 3.6); and the ability to intervene or stop by the suspension procedure, the non-regression test, and the interim harm-only stopping rule (Sections 3.6 and 6.3.8). The purpose of the mapping is to demonstrate that the oversight requirements most likely to be imposed on educational AI are satisfiable by an architecture designed for pedagogical reasons rather than retrofitted for compliance.

### 3.4 Ironies of automation and automation bias

The strongest theoretical warning about this architecture is also the oldest. Bainbridge's "Ironies of Automation" observed that automating routine work leaves humans responsible for the rare, difficult, and unpredictable cases—precisely those for which their degraded skill least prepares them [18]. Applied here: if the agents handle routine grading and calibration, teachers will encounter only anomalous profiles and escalated failures, and their capacity to judge those cases may decline through disuse.

The triage-driven escalation in Section 3.5 deliberately routes only anomalous cases to teachers, which is efficient and is exactly the arrangement Bainbridge warned about. Three design responses partially mitigate it: teachers review a stratified sample of routine decisions as well as escalations, so routine judgment is exercised; the decision-quality audit measures the accuracy of teacher judgments on sampled routine cases; and the end-of-cycle meta-cognitive review requires teachers to reason about aggregate patterns rather than individual cases, exercising a different and less easily degraded judgment.

The automation-bias literature [19,20] adds a second mechanism: humans monitoring automated systems tend to under-detect failures, particularly as reliability rises. A correction agent that is right 90% of the time will train teachers to accept its output, and the 10% will be harder to catch than if it were right 70%. The sampling audit and the disagreement protocol in Section 6.3.7 are designed with this in mind, and the audit is stratified to include cases the system is confident about as well as cases it is not.

### 3.5 Three levels of oversight

**Pre-cycle validation.** The teacher checks questionnaires and exercises against learning objectives before they reach students, enforcing pedagogical alignment and operationalizing the constructive-alignment specification from Section 2.4.

**In-cycle triage-driven escalation.** The tutorial teacher receives escalations triggered by pre-specified rules: divergence between psycho-technical and performance signals, low agent confidence, and the protective rule in Section 6.3.4. Escalations are triaged rather than randomly sampled, because random sampling under high volume produces rubber-stamping rather than judgment. A stratified sample of routine decisions is reviewed alongside escalations, for the reason given in Section 3.4.

**End-of-cycle meta-cognitive review.** The course lead examines aggregate trends, detects systematic bias, and revises the decision rules. This is where the system learns at the level of design rather than of individual students, and it is the mechanism by which the tracking criterion is maintained over time.

### 3.6 Structural safeguards

**Audit log.** Every agent decision is logged alongside the corresponding human decision, enabling accountability and providing data for the tracking-and-tracing audit. The log is append-only, and each entry references the version of the decision rules in force at the time. The log is written exclusively by the deterministic orchestrator (Section 4.1), not by any agent.

**Escalation procedure.** Divergence between psycho-technical and performance signals triggers human review, with specified reviewer, timeframe, and available actions.

**Pedagogical non-regression test.** Before each cycle, a sample of generated content is checked against the learning objectives specified under constructive alignment. Content that fails is regenerated or edited before deployment.

**Default-deny gate.** No agent output reaches a student until a human has approved it. The gate is enforced by the orchestrator, not by the teacher remembering to act; an output awaiting approval is withheld rather than released. This is a stronger commitment than a review process, because the failure mode of a review process is silent release when the reviewer is absent.

**Suspension procedure.** Any teacher can suspend the system's recommendations for an individual student or an entire section, with a stated reason, without requiring approval. Suspensions are logged and reviewed at the end of the cycle. This is the operational form of Article 14's requirement that the overseer be able to intervene in or stop the system [17].

### 3.7 Accountability model

Each error class carries an accountable human. A misgraded submission is the responsibility of the tutorial teacher who approved the correction agent's rubric, subject to the sampling audit that determines whether the error was detectable. A harmful profile is the responsibility of the course lead who approves the psycho-technical rules. A privacy breach is the responsibility of the institutional data controller (Section 5.2). An equity failure—systematic misfiring on accommodated or disadvantaged students—is the responsibility of the course lead and is reported as a design-validity threat rather than an implementation error. The audit log exists to support this allocation: it records what the agent decided, what the human approved, and what information was available at the time. This is a design commitment, not an empirical finding; whether teachers in practice experience these responsibilities as theirs is addressed by the interviews and decision-quality audits in Section 6.4.

### 3.8 Scalability of oversight: the linear bottleneck

The deepest tension in the design is that oversight does not scale the way the agents do. Agent capacity grows with compute; oversight capacity grows with tutorial hours, and tutorial hours grow linearly with enrolment. If meaningful oversight is required for legitimacy, and oversight capacity is linear in students, the architecture has a hard scaling ceiling that no amount of model improvement removes.

Three responses are available, and we state their trade-offs rather than recommending one. **Triage** reduces the number of decisions requiring review but concentrates review on the hardest cases—the Bainbridge problem [18]. **Aggregation** allows teachers to review patterns rather than individuals, which scales better but cannot discharge tracing for individual outcomes. **Accepting a lower oversight ratio** scales the system but weakens the claim that each decision is meaningfully controlled. The present design adopts triage plus aggregation and states its oversight ratio explicitly: one tutorial teacher per 50 students, escalation volume targeted at 3–7% of student-weeks, and routine sampling at 5% of decisions. If observed volume exceeds capacity, the design reduces coverage rather than allowing review quality to degrade silently, and the reduced coverage is reported as a limitation. This is a design parameter the pilot is intended to calibrate.

### 3.9 Epistemic status: legitimacy, not learning

We state a concession the reader should hold us to. **We do not claim that human oversight improves learning outcomes.** We claim it is a condition of legitimate deployment in a high-risk educational application [17] and of the tracking and tracing criteria being satisfied [16]. Whether intensive oversight also produces larger learning gains is a separate empirical question, addressed by the oversight-intensity arm and reported as RQ2.

The distinction matters because the evidence bases differ. The complementarity literature supports a claim about learning outcomes [5,9]; the automation-bias literature [19,20] and the AI Act [17] support claims about safety, accountability, and legitimacy. Blurring the two would allow a null result on RQ2 to be read as a refutation of the pillar, which it would not be. The pillar would survive a null RQ2 on legitimacy grounds while the complementarity claim narrowed to the conditions under which it has been demonstrated.

---

## 4. Pillar 3 — Multi-Agent Architecture

### 4.1 Why a multi-agent architecture

A single monolithic model asked to design questionnaires, score profiles, generate exercises, correct submissions, and track progress would produce opaque and difficult-to-audit behaviour. Recent work on educational multi-agent systems addresses this by separating decision-making from wording and by assigning specialized roles. The Ensemble of Specialized LLMs architecture, for example, uses a rules-based orchestrator to coordinate agents covering tutoring, assessment, feedback, scaffolding, motivation, and ethics, guided by an interpretable student model, enforcing constraints such as "attempt-before-hint" and logging per-turn agent traces. This separation improves reliability, controllability, and auditability.

The architecture here follows the same logic but is organized around the weekly customization cycle rather than dialogue. Each agent corresponds to a distinct function in the cycle, and each output passes through a human gate before affecting a student. The gates are specified in Section 3; this section specifies the machinery behind them.

A **deterministic orchestrator** sits between the agents and the student-facing interface. It is not a sixth decision-maker: its behaviour is fully specified by the rule set in Section 6.3.5 and the weekly-cycle specification in Section 4.3. Its role is to sequence agent handoffs, enforce the default-deny gate at each human barrier, and write the audit log. Locating sole write authority over the log in a deterministic component rather than in any individual agent preserves the tracing criterion in Section 3.2: the log cannot be edited by the same component whose decision it records. Agents do not exchange messages directly. Data moves through orchestrator-mediated handoffs into a state store that the orchestrator alone writes and reads, so that every inter-agent transfer is visible to the orchestrator and recorded in the log.

We note explicitly that controlled deployments of multi-agent educational systems with measured learning outcomes are, to our knowledge, absent from the published literature. This is simultaneously the architecture's novelty claim and its principal evidentiary weakness. The design is offered as a testable proposal, not a demonstrated intervention.

### 4.2 Agent roles

**Table 2. Agent roles and human safeguards**

| Agent | Role | Human safeguard |
|---|---|---|
| **Questionnaire Designer** | Generates initial and weekly questionnaires from course content and student history | Teacher approval before deployment |
| **Psycho-Technical Assessor** | Scores responses on psychological and technical criteria | Tutor review of divergent cases |
| **Exercise Generator** | Produces targeted supplementary exercises | Tutorial teacher validation and modification |
| **Correction Agent** | Grades exercises and provides formative feedback | Random human sampling and audit |
| **Longitudinal Synthesis** | Aggregates weekly data and updates the learner model | Periodic review by course lead |

Each agent is justified by what it frees the teacher to do. The Questionnaire Designer frees the teacher from item generation; the Assessor from routine scoring; the Exercise Generator from producing difficulty variants; the Correction Agent from first-pass grading; the Synthesis Agent from manual tracking. Teacher time is redirected toward interpretation, escalation, and pedagogical adaptation.

The orchestrator is not an agent and is not listed in Table 2. It carries no decision authority: every decision it sequences originates in an agent output and terminates in a human gate. The orchestrator has no discretionary parameters. Given the rule set in force and the approval state of a given output, its behaviour is determined; withholding is a consequence of the gate's default state rather than a judgement about the output. Discretion requires the capacity to vary behaviour within a range the specification leaves open, and the orchestrator has no such range. Its transparency—not its intelligence—is what the design depends on.

### 4.3 The weekly cycle

The cycle has four stages that produce student-facing output, plus a fifth function that closes the loop between weeks. The topology is specified in Figure C.

1. **Before the lecture.** The Questionnaire Designer generates a short questionnaire calibrated to the previous week's material and the student's evolving profile. The Psycho-Technical Assessor scores responses within the same stage, so that the profile used to calibrate this week's exercises is current before the tutorial.
2. **During the lecture.** The teacher receives anonymized aggregate profiles and adjusts emphasis, examples, and pacing. No individual-level psycho-technical data is displayed.
3. **In the tutorial.** The Exercise Generator produces supplementary exercises calibrated to each profile. The tutorial teacher reviews, modifies, or replaces them before distribution; the gate is default-deny, and unapproved exercises are withheld from students rather than released. A supervised block ensures at least 30% of weekly volume is completed under observation without external tools (Section 6.3.7).
4. **After the tutorial.** The Correction Agent grades and provides formative feedback. Concurrently, the Longitudinal Synthesis Agent updates each student's model from the week's outcomes and generates the calibration signal that feeds stage 1 of the next week. Synthesis does not wait for correction to be complete, because the model update draws on exercise outcomes as they arrive.
5. **Next week.** Stage 1 draws on the synthesis output carried forward from stage 4.

This operationalizes the frequency and granularity arguments from Section 2.3 and creates repeated points of teacher intervention rather than a single high-stakes decision at term's end.

![Figure C: The supervised cycle](https://cdn.hashnode.com/uploads/gql/6a92730f9a9aa7f72e74fdf4/b0d43398-8f60-4107-8700-211bdb601998.png)

**Figure C. The supervised cycle.** Four stages produce student-facing output — questionnaire and assessment, exercise generation, correction, and the tutorial-supervised block — and a fifth agent, Longitudinal Synthesis, closes the loop by carrying an updated learner model into the next week's questionnaire. The Longitudinal Synthesis Agent is drawn at the loop-closing point rather than as a fifth stage in the chain, because it operates concurrently with correction and its output is not itself student-facing. All five agents are sequenced by a deterministic orchestrator that carries no decision authority and is the sole writer of the audit log. Agents do not exchange messages directly; data moves through orchestrator-mediated handoffs into a state store the orchestrator alone writes and reads. Every agent output is followed by a default-deny human barrier: an unapproved output does not reach a student, and the pause is enforced by the orchestrator rather than by the teacher remembering to act. The audit log records the agent decision, the human approval, the information available at approval, the rule version in force, and any override reason. Escalation is cross-cutting rather than a stage: any agent may raise a flag, aggregated and triaged at a human barrier. The end-of-cycle review revises versioned decision rules through the orchestrator. The figure asserts three properties the prose cannot easily carry: that no agent touches another agent directly, that the audit-log writer is not a decision-maker, and that escalation is a channel rather than a box.

### 4.4 Failure modes

The architecture carries predictable failure modes, stated here because a design-science contribution is judged partly by whether it anticipates its own failures, and because the oversight checklist in Section 3.3 requires that overseers understand the system's limitations. A full taxonomy with detection signals and mitigations is provided in Supplementary Table S1. Three failure modes carry argumentative weight in this manuscript and are stated in text: **hallucinated exercises or factual errors**, detected through validation failure rates and mitigated by retrieval grounding and teacher edit; **miscalibrated difficulty**, detected by realized success rates outside the target band and mitigated by reselection; and **orchestrator defect**, addressed by the append-only, rule-versioned log described in Section 3.6. The remaining modes — sycophantic feedback, escalation flooding, teacher rubber-stamping, compounding error, detector false positives, and silent coverage reduction — are reported in Supplementary Table S1 with their detection signals and mitigations, and are cross-referenced from the sections that treat them.

---

## 5. Pillar 4 — Privacy-by-Design

### 5.1 Why multi-agent customization intensifies privacy risk

The architecture requires something most educational technologies avoid: **persistent, longitudinal, multi-instrument psycho-technical profiling**. The system must remember a student's self-efficacy, emotion-regulation strategies, curiosity, and locus of control across a semester and update those profiles weekly. This is the kind of high-resolution digital dossier that data-minimization principles are designed to constrain. Privacy is therefore not a compliance layer added after the pedagogical design; it is a condition of the design's legitimacy. If students distrust the system, they will not disclose accurate information and customization will rest on distorted data. If teachers cannot understand what data the system holds and why, they cannot meaningfully validate its recommendations.

### 5.2 Governance framework

The governance model draws on DPIA-based frameworks for AI in higher education, which organize privacy protection around rights-centric, lifecycle-oriented, context-sensitive, participatory, and human-centred principles [32]. Six operational commitments follow.

**Purpose limitation.** Psycho-technical data is used only for pedagogical customization, never for admissions, ranking, disciplinary decisions, or any secondary purpose. This boundary is stated in the student-facing notice and enforced in access controls.

**Data minimization.** Only instruments and behavioural signals required by the current decision rule are collected. A dimension that does not change an exercise recommendation is not collected.

**Differential privacy.** Aggregate analytics for dashboards and research are processed with DP so that individual profiles cannot be reverse-engineered from summary statistics. Individual-level profiles are protected not by DP but by access control, encryption at rest, retention limits, and contestability.

**Contestability.** Students can view their profile in interpretable form, challenge scores, and request human review. Because psycho-technical data can drive automated decisions about a learning trajectory, contestability is framed as a data-protection right under the applicable automated-decision-making provision [17], not as a courtesy.

**Right to refuse profiling without academic penalty.** Contestability presumes participation. A stronger commitment is required: a student may decline psycho-technical profiling entirely, with no academic consequence, receiving the performance-only path described in Section 6.3.8 (Arm P), which uses knowledge tracing and item difficulty alone and requires no affective disclosure. The system is designed so that the performance-only path is a complete and legitimate instructional arrangement, not a degraded one. Refusal is a binary flag, not visible to teaching staff, and reported in aggregate. The tension this creates — a possible two-tier arrangement if Arm T proves superior — is stated as an open ethical issue in Section 7.

**Role clarity.** Controller and processor responsibilities between institution and any vendor are specified in advance, including retention periods, deletion procedures, and breach-notification obligations.

**Forward-looking requirement: federated learning.** Where a future deployment involves training across sections or cohorts, training is conducted locally and only model updates are transmitted. **The current design does not require cross-institutional federation, and there is no data flow in this architecture that federation protects.** We list it as a forward-looking requirement rather than an operational commitment, because an item that is counted among the controls without a corresponding data flow would misrepresent what is actually in place. The purpose of naming it here is to state what would be needed if the architecture were extended across institutions, not to claim that the extension has been made.

### 5.3 Data-flow reconciliation

The commitments above are often asserted at the level of principle without a data-flow analysis. Supplementary Table S2 specifies which mechanism protects which data at which stage. Two points require statement in the main text. First, the individual-level profile the system requires is **not** protected by differential privacy; DP applies to the analytics layer, and the individual profile is protected by access control, retention limits, and contestability. Second, federated learning has no corresponding data flow in this design, as stated in Section 5.2.

### 5.4 Label minimization for vulnerable students

Psycho-technical profiles of students in difficulty approach special-category data in sensitivity, and a "low self-efficacy" label displayed outside the immediate pedagogical relationship can stigmatize. Individual psycho-technical scores are never displayed to teachers, advisors, or administrators. Teachers see only actionable signals: an escalation notice, a recommended adjustment, and the evidence category that triggered it. No profile persists across courses, and none is available to any function outside the weekly cycle. These data are covered by the same purpose-limitation and contestability guarantees as the rest of the profile and are not available to any welfare, disciplinary, or advising process.

### 5.5 Privacy as an enabler of teacher oversight

The governance framework is often presented as a constraint on personalization. Here it is also an **enabler**. Teachers cannot validate profiles they cannot interpret, and students will not disclose accurately if they fear misuse. Purpose-limited, transparent, and contestable data flows are pedagogically functional, not merely legally required. Privacy-by-design makes teacher oversight feasible at scale, and teacher oversight makes customization educationally legitimate.

---

## 6. Evaluation Design

### 6.1 Research questions

**RQ1 (customization, primary).** Does the supervised multi-agent cycle produce learning gains beyond high-quality teaching without AI customization, benchmarked against the two-sigma aspiration and recent meta-analytic estimates [1,2,3,4,6]?

**RQ2 (human control, primary).** Does oversight intensity produce a dose–response relationship with learning outcomes, and does the system satisfy the tracking and tracing criteria in observed operation [16]?

**RQ3 (teacher role).** How does teacher time allocation shift, and does net workload decrease or increase? What is the observed oversight ratio, and does coverage degrade silently?

**RQ4 (privacy).** Do privacy concerns predict engagement, disclosure accuracy, and refusal rates, and does the governance model mitigate these effects?

RQ1 and RQ2 are both primary. RQ2 being primary is a consequence of treating human control as a pillar: a claim that prominent cannot be a secondary analysis.

### 6.2 Design

The study is a cluster-randomized stepped-wedge trial across tutorial sections, with two embedded trials: a within-system A/B of the decision rules and an oversight-intensity factorial arm.

**Stepped-wedge structure.** Sections are randomized to the order in which they receive the system; all eventually receive it. This addresses the self-selection and instructor-enthusiasm confounds of a matched quasi-experiment and accommodates the institutional constraint that no section can be permanently denied a potentially beneficial intervention. The primary cross-sectional comparison is between sections that have and have not received the system at each wave.

**Oversight-intensity factorial arm.** A 2×2 manipulation of (AI customization on/off) × (teacher oversight intensive/light) tests RQ2. Intensive oversight means the full protocol in Section 3.5 with 5% routine sampling and a 3–7% escalation target. Light oversight means escalation only, with no routine sampling and reduced teacher time. If light oversight produces outcomes equivalent to intensive, oversight is decorative with respect to learning, and the pillar's claim narrows to legitimacy alone as anticipated in Section 3.9.

**Duration.** One 13-week semester with a week-14 follow-up. Novelty effects that inflate short ITS studies are reduced but not eliminated; the delayed post-test and cross-sectional stepped-wedge structure provide additional control.

**Attrition.** Attrition is assumed higher for the stepped-wedge comparison (15%) than for the individually randomized A/B (12%) because whole sections can withdraw from the sequence, whereas an individual student's withdrawal does not remove a section from the design.

**Power.** Assuming six sections of 50 students, 15% attrition, an ICC of 0.10 at section level, and the within-student SD in Section 6.3.8, the MDE for the cross-sectional comparison is approximately *d* = 0.30. The within-system A/B has a lower MDE because it is individually randomized. The factorial arm has a larger MDE than either and is reported as such: a null there is not evidence of equivalence, and we state this in advance rather than interpreting it post hoc.

### 6.3 The Decision Engine

#### 6.3.1 Rationale for temporal separation

The engine rests on a claim that is both psychometric and architectural: **instructional decisions operating at different time scales require measures with different temporal properties**. A weekly difficulty adjustment is a within-person decision requiring an instrument whose variance is substantially within-person. A semester-level scaffolding register is a between-person decision that tolerates—indeed benefits from—the greater stability of trait measurement. Conflating the two produces the failure of acting on trait measurement error at weekly cadence.

We therefore separate a **fast layer** governing proximal decisions (difficulty, item selection, hint availability, session length) from a **slow layer** governing distal decisions (scaffolding intensity as default register, feedback tone, emotional framing). The layers are instrumented differently, updated on different schedules, and arbitrated by an explicit rule. This temporal structure is itself a contribution: prior adaptive systems have typically used a single measurement cadence and have not articulated why a given construct belongs at a given time scale. The full two-layer specification, including the aggregation window and the precedence rules, is summarized in Supplementary Figure S1.

#### 6.3.2 The fast layer

**Knowledge-component mastery.** Bayesian Knowledge Tracing [21] per knowledge component, with deep knowledge tracing [22] as a robustness check. Knowledge components are derived from intended learning outcomes under Section 2.4. Item difficulty is estimated with a one-parameter logistic model anchored on a proctored week-1 placement diagnostic.

**Item-level difficulty fit.** Rather than a global difficulty label, the engine estimates for each student and candidate item the predicted probability of correct response, and selects items whose predicted success lies within a 0.70–0.85 band, consistent with ITS convention and with formal learning models deriving an optimal error rate under strong assumptions [23].

**State-level affective measures.** Two short-form state instruments are administered weekly before the tutorial: a state curiosity measure adapted from the state version of the Curiosity and Exploration Inventory, and a state affect measure adapted from PANAS [24]. A three-item weekly state self-efficacy adaptation is **locally developed** from the New General Self-Efficacy Scale [25]; its weekly reliability will be estimated in the pre-pilot and reported in the pre-registration. If weekly reliability falls below 0.70, the self-efficacy term is removed as a rule trigger in both rules 2 and 3. Rule 3 is suspended. Rule 2 reverts to a performance-only protective trigger — realized success below the target band for two consecutive weeks — which issues a teacher notification but no difficulty ceiling, because the ceiling was justified by the affect signal and that signal is no longer trustworthy. We prefer this over a silent downgrade to notification alone: the suspension is logged, and the course lead reviews it at the end of the cycle.

**Aggregation policy.** Single administrations are never decision inputs. State scores enter only as a **trailing three-week exponentially weighted mean** (weights 0.5, 0.3, 0.2), and a trigger fires only when the current score deviates from the student's own trailing mean by more than one standard error of measurement. This converts an absolute-score rule into a **within-person deviation rule**, more defensible psychometrically and more robust to the volatility state measures introduce by design. The window and SEM band are pre-registered parameters.

#### 6.3.3 The slow layer

Three trait instruments are administered twice—intake (week 1) and term-end (week 13)—and nowhere between: the General Self-Efficacy Scale [26], a Locus of Control scale, and the Emotion Regulation Questionnaire [27]. They do not select difficulty. They set **default registers**: initial scaffolding intensity, default feedback framing, tolerance for open-ended versus structured formats, and the emotional-load ceiling for the student's first weeks. Term-end administration provides an outcome for RQ4 and tests whether registers should be revised for a subsequent course.

We make no claim that these traits predict optimal difficulty. That would be an aptitude–treatment interaction of exactly the kind the field has failed to replicate [28]. The exception is expertise reversal (rule R2), a replicated within-domain interaction [15] whose transfer from worked examples to AI-generated difficulty is stated as motivational rather than warranting in 6.3.5.

#### 6.3.4 Arbitration between layers

The layers can conflict. The arbitration rule is stated in advance and is not model-learned.

1. **Fast layer has default authority** over proximal decisions, unless rules 2 or 3 fire.
2. **Slow layer has override authority in one protective configuration.** If state self-efficacy remains more than one SEM below the student's own intake baseline for **two consecutive weeks** *and* realized success rate falls below the target band for the same two weeks, the engine imposes a difficulty ceiling (predicted success capped at 0.85), reduces session length by one third, and **escalates to the tutorial teacher**. This is a protective rule, not a personalization rule.
3. **Affect-only soft escalation.** If state self-efficacy is one SEM below baseline for two consecutive weeks **without** sub-band performance, the engine issues a **teacher notification only**—no ceiling, no session reduction. This catches the compensating high-effort student whose performance masks deteriorating affect.
4. **Precedence.** Where the guidance-reduction rule (R2) and the protective ceiling conflict, **the protective ceiling wins** for its duration. The expertise-reversal rationale does not override a safeguarding rule.
5. **No other override exists.** Other conflicts are logged and reported as diagnostics.
6. **Expected trigger rate.** 3–7% of student-weeks. Below 1% indicates the rule is inert; above 15% indicates miscalibration.

#### 6.3.5 Decision rules: grounded versus hypothesis

Every rule carries an epistemic annotation. Rules marked **grounded** are licensed by a named mechanism and cited literature. Rules marked **hypothesis** are fed to the A/B test and are not assumed effective in the manuscript's argument.

**Table 3. Decision rules with epistemic status**

| Rule | Trigger | Action | Status | Mechanism or test |
|---|---|---|---|---|
| R1 | Predicted success outside 0.70–0.85 | Reselect within band | **Established practice, limited causal warrant** | ITS convention [21,29]; theoretical motivation from [13,23]. Band is a testable parameter. |
| R2 | Mastery > 0.95 on component | Reduce guidance | **Grounded (motivational)** | Expertise reversal [15]. Established with worked examples, not AI-generated difficulty. |
| R3 | Mastery < 0.50 on prerequisite | Insert prerequisite remediation | **Grounded** | Cognitive load and prior knowledge [14] |
| R4 | Trailing state curiosity high, affect positive | Increase open-ended, transfer-oriented items | **Hypothesis** | Tested in Arm T |
| R5 | Trailing curiosity low, affect flat | Increase structure, shorten sessions | **Hypothesis** | Tested in Arm T |
| R6 | State self-efficacy low + sub-band performance (2 weeks) | Difficulty ceiling, session reduction, escalation | **Hypothesis (protective)** | Guardrail, not efficacy |
| R7 | High performance + low transfer | Substitute novel-context items | **Hypothesis** | Tested in Arm T |

Only R2 and R3 are presented as evidence-based, and R2 carries the motivational caveat. R1 is established practice with limited causal warrant. R4–R7 are testable propositions, and the manuscript's efficacy claims do not depend on them. We found no RCT establishing a 0.70–0.85 band at weekly cadence in university content; the band is a design parameter and its width is a candidate for future factorial testing.

#### 6.3.6 Cold-start protocol

Weeks 1–2 precede any usable performance signal, so the engine operates in a declared provisional mode.

- **Week 1**: a proctored placement diagnostic (30 items across knowledge components) establishes difficulty anchors and initial mastery priors, initializes BKT with population priors and wide variance, and serves as a stratification variable for randomization.
- **Weeks 1–2**: difficulty is fixed at the population median per component with a deterministic staircase (two consecutive successes → one step harder; two consecutive failures → one step easier). No state or trait input is used for difficulty.
- **Week 3 onward**: the fast layer takes over. The provisional flag is logged and reported; weeks 1–2 are excluded from primary outcome analyses.
- **Baseline probe**: administered in **week 2**, during cold-start, when item assignment follows the deterministic staircase and is identical across arms. This placement is deliberate: a week-3 baseline would be administered after the arms have diverged, and any immediate effect or disruption of the Arm T rules would be absorbed into the baseline, biasing the estimated treatment effect toward null.

The cold-start protocol is stated here rather than in an appendix because it determines what the first two weeks actually test, and because a reviewer is entitled to know that the system's early behaviour is not personalized.

#### 6.3.7 Contamination detection and the integrity floor

Supplementary exercises are completed partly outside supervised hours, and a student may use an external language model. This threatens not merely grading validity but the **calibration signal itself**: if success rates and response times reflect prompt proficiency rather than learning, the fast layer calibrates on noise and the error compounds weekly.

**Structural.** The weekly tutorial includes a supervised block in which at least 30% of weekly volume is completed under observation with no external tools. Calibration draws preferentially on supervised items; unsupervised items contribute to grading but are weighted at 0.5 in the mastery update. **Supervised completion is load-bearing, not a mitigation appended to the design.** A design in which all exercises are unsupervised cannot support performance-based calibration, and the fast layer would have to be abandoned.

**Detectional.** Each unsupervised submission carries a response-time signature. A record is flagged when three conditions co-occur: completion time below the 25th percentile of the item's expected time distribution, no revision or navigation events, and accuracy uniform across difficulty strata. Flagged records are excluded from the calibration signal—not from grading, and not from any disciplinary process. The flag is an input to the Synthesis Agent, not an accusation mechanism.

**Detector validation.** Before the main study, the detector is validated in a two-week pre-pilot with known honest completion under supervision and known LLM-assisted completion in a controlled task. Sensitivity and specificity are reported in the pre-registration, and the thresholds are tuned on the pre-pilot rather than asserted. The three-condition flag will produce false positives among strong, efficient students; false-positive rates are reported by placement quartile, and flagging is a **weighting decision, not an accusation**. Flagged students receive no penalty and no notification.

**Integrity floor.** If more than 20% of a student's unsupervised weekly records are flagged, that student's calibration signal for the affected week reverts to supervised items only. If the cohort-level flag rate exceeds 20% for two consecutive weeks, this is reported as a design-validity threat in the pre-registered analysis, and the affected weeks are excluded from the primary outcome. The 20% floor is a governance rule chosen for interpretability, not derived from the detector's operating characteristics; its rationale is reported alongside sensitivity and specificity.

**Disagreement protocol.** When the detector and the supervised block disagree, **the supervised block takes precedence for calibration purposes**. The disagreement is logged and reported as a detector-calibration diagnostic.

**Accommodation protocol.** Students with approved accommodations are identified only by a binary flag, never by accommodation type. The detector is suspended for flagged students, whose calibration signal draws exclusively from supervised probe items. The protective session-length reduction is applied only in consultation with the disability support office and never in a way that reduces an accommodated minimum. Time-based indicators are excluded from calibration for flagged students. We report the number of flagged students and the proportion of their calibration signal drawn from supervised items, because a design that systematically misfires on accommodated students would reproduce the inequity it aims to address.

#### 6.3.8 The within-system A/B trial

The A/B tests whether state- and trait-informed decision rules outperform a performance-only baseline. It is pre-registered separately and reported as a secondary analysis of the parent study. Full protocol detail is in Supplementary Appendix A; the design is summarized here.

**Design.** Individually randomized, stratified by section and placement quartile, 1:1 allocation, with the student as the randomization unit because decision rules govern an entire trajectory. Allocation is concealed until after the placement diagnostic. Students and teachers are blind to arm; the engine is not. Spillover through peer discussion is acknowledged, with cluster-robust standard errors as a sensitivity analysis. Teacher escalation behaviour is a shared channel: the same teacher responds to protective-rule escalations from both arms, so teacher-mediated effects cannot be arm-isolated; the protective rule is therefore treated as a guardrail rather than an efficacy mechanism, with response times and escalation volume reported by arm.

**Arms.** Arm **P** (performance-only): R1, R2, R3, R6. Arm **T**: R1–R7. Arm P is also the path available to students who decline profiling (Section 5.2). Instrument administration is identical across arms: both complete all weekly state instruments and both trait administrations, with Arm P differing only in that scores do not enter item selection. This preserves measurement symmetry and ensures the instruments retain data as outcome measures under the falsification clause below.

**Primary outcome: mastery gain on the common supervised probe.** The probe is a fixed item set administered to both arms during the supervised block of Section 6.3.7, drawn from a bank the engine never accesses, selects from, or sees. Parallel forms for weeks 2, 7, and 12 are equated via anchor items using a one-parameter logistic model, with difficulty parameters estimated from the placement diagnostic and pre-pilot and held fixed. Each probe includes closed- and open-format items so that neither arm's item mix is favoured. Mastery is estimated per knowledge component from probe responses alone using a joint IRT change model with item parameters fixed across waves. Where BKT is used for manipulation checks, learning and slip parameters are estimated **pooled across arms**; fitting separately by arm would reintroduce a differential-measurement channel.

The outcome is non-circular by construction: the engine does not select, see, or optimize probe items, both arms receive identical items, and mastery is estimated from a measure the treatment cannot manipulate through item selection. The probe is also the supervised block already required by Section 6.3.7, so it adds no student time beyond the integrity floor. Each probe contains at least six items per knowledge component, with smaller components aggregated into composites; realized counts are reported. Anchor items are drawn from a reserved pool never used for instruction and never released; items are rotated across sections, and a post hoc exposure index is reported.

**Why the difficulty-fit index is demoted.** The difficulty-fit index measures whether the model's predictions matched outcomes on items the model selected. It is a manipulation check, not an efficacy outcome, because an arm that narrows its item mix can improve fit without improving learning, and because the rules systematically alter the realized outcome distribution the index measures. It is retained as a secondary manipulation check with this circularity stated explicitly.

**Primary analysis.** ANCOVA with week-12 probe mastery as outcome and week-2 probe mastery as covariate, adjusting for placement quartile and section. Change scores are reported as sensitivity only, because the reliability of a difference is lower than of either component and gain scores correlate spuriously with baseline [30].

**Secondary outcomes and guardrails.** Secondary: difficulty-fit index; delayed transfer at week 14 on blinded external items; state-affect trajectory. Guardrails: GSE change from intake to term-end tested for non-inferiority at 0.20 SD; attrition; engagement; assisted-to-unassisted performance gap on the probe; teacher escalation volume and response time.

**Estimand and missing data.** The estimand is the intention-to-treat effect of arm on week-12 probe mastery. Intermittent probe absence is expected; the primary mixed-effects specification uses all available waves under a missing-at-random assumption, stated explicitly rather than relying on complete-case analysis. Because absence may not be MAR—Arm T's rules alter session length and could alter attendance—a tipping-point sensitivity analysis specifies the departure from MAR at which the conclusion would reverse.

**Power.** Assuming 300 students, 12% attrition, and a within-student SD of probe mastery gain set at 0.18—**a pilot-derived value the pre-registration will update before unblinding**—the MDE at 80% power (α = .05, two-sided) is approximately *d* = 0.26, with sensitivity analyses at SD = 0.15 and 0.22. Rule-level effects will be smaller and are not powered for confirmatory inference.

**Pre-specified subgroup analysis.** Because the rules are designed to benefit low-prior-knowledge students disproportionately, a treatment-by-placement-quartile interaction is pre-specified as a secondary analysis with the bottom quartile as subgroup of interest. This analysis is exploratory and underpowered: with 300 students, the bottom quartile contains roughly 75, and the MDE for the interaction is substantially larger than the main-effect MDE. The estimate and its confidence interval are reported in full and are not used to reinterpret a null main effect as a positive finding.

**Stopping rules.** One interim analysis at week 6, reviewed by an independent monitor, for harm only: a guardrail breach on the GSE non-inferiority margin, or an attrition differential exceeding 10 percentage points. No stopping for efficacy.

**Interpretation committed in advance.** If Arm T does not outperform Arm P on probe-estimated mastery gain, the state- and trait-informed rules are reported as ineffective for the average student, and the architectural claim is revised to a performance-only decision engine with the trait and state instruments retained as outcome measures only. A positive bottom-quartile interaction in the absence of a main effect does not rescue the average-effect claim; it narrows it to a claim about low-prior-knowledge students, reported as a hypothesis-generating finding requiring replication in a trial powered for that subgroup. The difficulty-fit index result, whatever it shows, does not rescue the claim. This is the falsification condition for the customization mechanism.

### 6.4 Teacher role, privacy, and tracking measurement

Teacher time-use is measured through structured diaries and NASA-TLX workload ratings. Decision quality is assessed through expert re-rating of a stratified sample of validations that includes routine cases as well as escalations, so that automation-bias and skill-atrophy concerns are measured rather than assumed [18,19]. The observed oversight ratio is computed weekly as reviewed decisions per student, with any reduction below the stated threshold logged and reported as a limitation.

Privacy concerns are measured with the IUIPC scale [31], disclosure accuracy through comparison of self-reported psycho-technical scores with behavioural signals, and engagement through completion and response latency. Consent comprehension is assessed with a brief post-consent quiz. Contestation and refusal rates are logged and reported in aggregate, with refusal treated as a primary descriptive outcome of the governance model rather than as missing data.

The tracking and tracing criteria (Section 3.2) are operationalized as an audit conducted twice (weeks 6 and 12) and reported under RQ2. For a stratified random sample of 40 decisions per wave—drawn across escalation and routine categories and across both oversight-intensity arms—an independent rater blind to condition assesses the two questions stated in Section 3.2. Inter-rater reliability is established on a calibration set before the first wave. The audit yields proportions meeting each criterion with confidence intervals and is reported descriptively rather than tested against a threshold. Low tracking would indicate the system's behaviour has drifted from teacher-approved reasons, a design failure regardless of learning outcomes; low tracing would indicate accountability has diffused, a legitimacy failure regardless of learning outcomes. The audit is the empirical form of the pillar: it is cheap, uses data the system already generates, and tests the claim the title makes.

### 6.5 Pre-registration

The full protocol—primary and secondary outcomes, MDE with attrition assumptions, stopping rules, detector validation results, state self-efficacy reliability from the pre-pilot, the tracking-and-tracing audit protocol and calibration procedure, and the analysis code plan—is pre-registered before the main study begins. The A/B is pre-registered separately.

---

## 7. Discussion and Limitations

We state each limitation briefly here and cross-reference the section that develops it.

**Complementarity is not automatic, and oversight may be decorative with respect to learning** [5,9]. RQ2 is primary precisely so that this failure, if it occurs, is detected rather than assumed away (Sections 2.2, 3.9).

**Teacher workload and skill atrophy.** The ironies-of-automation literature predicts that concentrating human judgment on anomalous cases degrades the judgment needed to handle them [18,19]; net teacher time, decision quality on sampled routine cases, and the observed oversight ratio are measured as primary outcomes (Sections 3.4, 6.4).

**Orchestrator defect and audit-log integrity.** Because the deterministic orchestrator is the sole writer of the audit log, log integrity depends on a single component; the log is append-only and rule-versioned so that a defect is detectable rather than invisible (Section 4.1). This is a commitment to be verified in the pilot, not a property guaranteed by the architecture.

**The privacy–personalization trade-off and the refusal right.** The right to refuse profiling without penalty creates the possibility of a two-tier arrangement if Arm T proves superior. We accept this tension rather than resolving it by making participation compulsory, and flag it as the most serious unresolved ethical issue in the design [32]. Trial results will make the tension more acute if the state- and trait-informed rules are shown to work (Sections 5.2, 6.3.8).

**The equity claim is statistically fragile at this sample size.** The subgroup analysis is pre-specified but underpowered, and the manuscript does not rely on it for its headline claim (Section 6.3.8).

**Assessment contamination.** Take-home exercises are vulnerable to external models, and the supervised block is load-bearing rather than supplementary; if contamination exceeds the integrity floor, the fast layer's calibration signal degrades and the central mechanism is at risk (Section 6.3.7).

**The scaling ceiling of oversight.** Oversight capacity grows linearly with students while agent capacity does not. This is the deepest structural limitation and it is not solved by better models (Section 3.8).

**Multi-agent educational systems have no controlled deployments with measured outcomes.** The architecture is novel, and novelty is a liability as well as a contribution (Section 4.1). The design is a testable proposal whose value will be determined by the trial, not by the elegance of its specification.

**The human-control pillar's evidence base is about legitimacy, not learning.** A null result on RQ2 narrows the complementarity claim but does not refute the pillar, whose warrant comes from accountability and safety [17] rather than from effect size (Section 3.9).

**Generalizability.** A single-course trial cannot support broad claims about AI customization as a category. Replication across disciplines and contexts is necessary before the architecture can be recommended at scale.

---

## 8. Conclusion

Bloom's two-sigma finding established what individualized instruction can achieve and why it matters [1]. It also established a constraint the intervening decades have not removed: the effect came from human tutors, and human tutoring does not scale by itself. AI-driven customization is valuable not because it reproduces the tutor, but because it can extend parts of the tutoring function—frequency, granularity, consistency—while the teacher retains the interpretive and accountable core of teaching [5].

The architecture proposed here is organized around four pillars. Customization is the pedagogical goal, anchored in instructional alignment [11,12] rather than in the assumption that personalization is beneficial. Meaningful human control is the authority structure, specified through tracking and tracing [16] rather than asserted through the presence of a human. Multi-agent design is the mechanism that makes customization operationally feasible without collapsing into an opaque monolith, with the deterministic orchestrator as the component that preserves tracing. Privacy-by-design is the condition that makes persistent profiling trustworthy, including the right to decline it without penalty [17,32]. None of the four is sufficient alone, and the ordering—goal, authority, mechanism, condition—is itself part of the argument.

The design is not a claim that AI has solved Bloom's problem. It is a claim about how to extend teaching without displacing it, stated in a form that can be tested, falsified, and revised. If the trial shows the state- and trait-informed rules add nothing to a performance-only baseline, the architecture narrows to the performance layer and the claim is revised accordingly. If it shows benefit concentrated among low-prior-knowledge students, the claim narrows to that population and a subgroup-powered replication is required. If the oversight-intensity arm shows no dose–response, the complementarity claim narrows while the legitimacy argument for human control stands on its own grounds. The falsification conditions are stated in the manuscript rather than in an appendix because a design that cannot fail cannot be evaluated.

---

## References

[1] Bloom, B. S. (1984). The 2 sigma problem: The search for methods of group instruction as effective as one-to-one tutoring. *Educational Researcher, 13*(6), 4–16.

[2] Ma, W., Adesope, O. O., Nesbit, J. C., & Liu, Q. (2014). Intelligent tutoring systems and learning outcomes: A meta-analysis. *Journal of Educational Psychology, 106*(4), 901–918.

[3] VanLehn, K. (2011). The relative effectiveness of human tutoring, intelligent tutoring systems, and other tutoring systems. *Educational Psychologist, 46*(4), 197–221.

[4] Burneo, A., Dinarte-Diaz, L., Lopez, C., & Molina, E. (2026). *Can EdTech close learning gaps? Global evidence from digital interventions*. World Bank.

[5] Holstein, K., & Aleven, V. (2022). Designing for human–AI complementarity in K-12 education. *AI Magazine, 42*(2), 17–30.

[6] Zhang, J., Li, Z., Wu, Y., & Huang, Y. (2026). Synthesizing the effects of AI-driven adaptive learning platforms on students' academic achievement: A meta-analysis. In *Proceedings of the ACM Conference*.

[7] Pane, J. F., Steiner, E. D., Baird, M. D., & Hamilton, L. S. (2015). *Continued progress: Promising evidence on personalized learning*. RAND Corporation.

[8] Buçinca, Z., Malaya, M. B., & Gajos, K. Z. (2021). To trust or to think: Cognitive forcing functions can reduce overreliance on AI in AI-assisted decision-making. *Proceedings of the ACM on Human-Computer Interaction, 5*(CSCW1), 1–21.

[9] Holstein, K., McLaren, B. M., & Aleven, V. (2019). Co-designing a real-time classroom orchestration tool to support teacher–AI complementarity. *Journal of Learning Analytics, 6*(2), 27–52.

[10] Levin, H. M., McEwan, P. J., Belfield, C., Bowden, A. B., & Shand, R. (2018). *Economic evaluation in education: Cost-effectiveness and benefit-cost analysis* (3rd ed.). SAGE.

[11] Biggs, J. (1996). Enhancing teaching through constructive alignment. *Higher Education, 32*(3), 347–364.

[12] Koedinger, K. R., Corbett, A. T., & Perfetti, C. (2012). The Knowledge-Learning-Instruction framework: Bridging the science–practice chasm to enhance robust student learning. *Cognitive Science, 36*(5), 757–798.

[13] Bjork, E. L., & Bjork, R. A. (2011). Making things hard on yourself, but in a good way: Creating desirable difficulties to enhance learning. In M. A. Gernsbacher et al. (Eds.), *Psychology and the real world*. Worth Publishers.

[14] Sweller, J., van Merriënboer, J. J. G., & Paas, F. (2019). Cognitive architecture and instructional design: 20 years later. *Educational Psychology Review, 31*(2), 261–292.

[15] Kalyuga, S., Ayres, P., Chandler, P., & Sweller, J. (2003). The expertise reversal effect. *Educational Psychologist, 38*(1), 23–31.

[16] Santoni de Sio, F., & van den Hoven, J. (2018). Meaningful human control over autonomous systems: A philosophical account. *Frontiers in Robotics and AI, 5*, 15.

[17] European Parliament and Council of the European Union. (2024). *Regulation (EU) 2024/1689 laying down harmonised rules on artificial intelligence (Artificial Intelligence Act)*. Official Journal of the European Union.

[18] Bainbridge, L. (1983). Ironies of automation. *Automatica, 19*(6), 775–779.

[19] Parasuraman, R., & Riley, V. (1997). Humans and automation: Use, misuse, disuse, abuse. *Human Factors, 39*(2), 230–253.

[20] Parasuraman, R., Molloy, R., & Singh, I. L. (1993). Performance consequences of automation-induced "complacency." *International Journal of Aviation Psychology, 3*(1), 1–23.

[21] Corbett, A. T., & Anderson, J. R. (1995). Knowledge tracing: Modeling the acquisition of procedural knowledge. *User Modeling and User-Adapted Interaction, 4*(4), 253–278.

[22] Piech, C., Bassen, J., Huang, J., Ganguli, S., Sahami, M., Guibas, L. J., & Sohl-Dickstein, J. (2015). Deep knowledge tracing. *Advances in Neural Information Processing Systems, 28*.

[23] Wilson, R. C., Shenhav, A., Straccia, M., & Cohen, J. D. (2019). The eighty five percent rule for optimal learning. *Nature Communications, 10*, 4646.

[24] Watson, D., Clark, L. A., & Tellegen, A. (1988). Development and validation of brief measures of positive and negative affect: The PANAS scales. *Journal of Personality and Social Psychology, 54*(6), 1063–1070.

[25] Chen, G., Gully, S. M., & Eden, D. (2001). Validation of a new general self-efficacy scale. *Organizational Research Methods, 4*(1), 62–83.

[26] Schwarzer, R., & Jerusalem, M. (1995). Generalized self-efficacy scale. In J. Weinman, S. Wright, & M. Johnston (Eds.), *Measures in health psychology: A user's portfolio*. NFER-NELSON.

[27] Gross, J. J., & John, O. P. (2003). Individual differences in two emotion regulation processes: Implications for affect, relationships, and well-being. *Journal of Personality and Social Psychology, 85*(2), 348–362.

[28] Pashler, H., McDaniel, M., Rohrer, D., & Bjork, R. (2008). Learning styles: Concepts and evidence. *Psychological Science in the Public Interest, 9*(3), 105–119.

[29] Koedinger, K. R., & Aleven, V. (2007). Exploring the assistance dilemma in experiments with cognitive tutors. *Educational Psychology Review, 19*(3), 239–264.

[30] Lord, F. M. (1967). A paradox in the interpretation of group comparisons. *Psychological Bulletin, 68*(5), 304–305.

[31] Malhotra, N. K., Kim, S. S., & Agarwal, J. (2004). Internet users' information privacy concerns (IUIPC): The construct, the scale, and a causal model. *Information Systems Research, 15*(4), 336–355.

[32] Slade, S., & Prinsloo, P. (2013). Learning analytics: Ethical issues and dilemmas. *American Behavioral Scientist, 57*(10), 1510–1529.

---

## Supplementary Materials (not included in word count)

**Figure S1.** Two-layer decision engine: fast and slow layers, aggregation window, arbitration and protective precedence.
**Table S1.** Full failure-mode taxonomy with detection signals and mitigations.
**Table S2.** Data-flow reconciliation by stage, mechanism, and limitation.
**Table S3.** Exact effect sizes and source notes corresponding to Figure A. Where a source reports non-significance rather than an interval, this is noted; no interval is reconstructed.
**Appendix A.** Full within-system A/B protocol: randomization procedure, arm specification, probe construction, equating design, analysis code plan, and pre-registration checklist.
**Appendix B.** Tracking-and-tracing audit instrument and rater training protocol.

**Reproducibility note.** All figures are generated from scripts in which every plotted value is a hard-coded entry in a data block, and every label is a controlled string. Each value in the script carries a comment naming the sentence it supports, and each figure is referenced from the sentence that depends on it, so that figure and prose can be audited against each other across revisions. Figures are legible in greyscale, with hollow/filled and solid/dashed carrying the load rather than colour, and are set in a widely available open font family so that regeneration on another machine does not reflow labels.
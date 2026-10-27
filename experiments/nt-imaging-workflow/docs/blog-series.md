# Three-part blog series source outlines

## Part 1 — Why a governed workflow, not an agent swarm

- Hook: a useful local imaging demonstration needs explicit failure paths more than autonomous agents.
- Intended scope: one supported chest-radiograph artifact, structured drafting, human-supervised export; research only.
- Reusing a local oMLX foundation without rebuilding services; local inference reduces unnecessary data movement but does not make the whole Mac isolated.
- State machine walkthrough and terminal states; typed state as the contract between nodes.
- Deterministic policy versus model-assisted drafting, visual consistency, and text quality; what each gate does not prove.
- Supported imaging contract and why whole-study CT/MRI needs a different pipeline.
- Threat model: PHI, parser abuse, embedded instructions, malformed output, replay, memory limits, and public exposure.
- Test philosophy: attack routing and export before polishing UI; no clinical claims from synthetic workflow tests.

## Part 2 — Building and attacking the LangGraph implementation

- `AgentState`, strict report/review/decision schemas, and safe errors.
- Conditional edges that make unsafe transitions impossible; independent gate statuses.
- Versioned PHI screening with local Apple Vision OCR and fail-closed receipts; limitations, not anonymization guarantees.
- Fixed prompts, strict JSON parsing, one bounded syntax repair, total call budgets, and concise prior feedback.
- Grounding failure cannot be erased by quality review; exhaustion goes to human review.
- `interrupt()` and why export belongs in a separate node after resume.
- Checkpoint namespaces, idempotency keys, atomic writes, and tamper-evident demonstration audit events.
- Failure-path test catalogue and genuine mock-labelled screenshots; real-model evidence is distinct.

## Part 3 — Running a credible local showcase

- Start the durable FastAPI/worker console; inspect checkpoints, nodes, preparation, and model receipts in the local graph inspector without hosted Studio.
- Reviewer experience: derived image, draft, provenance, independent statuses, approval/rejection, downloads.
- Real discovered model IDs and doctor checks; no silent mock fallback or clinical-quality assertion.
- Evidence manifest: commands, versions, fixture/export/screenshot hashes, test totals, and known limitations.
- Public-sector value as inspectable governance and recoverable state, not autonomous diagnosis.
- A technical foundation for a governed pilot, subject to clinical, security, legal, regulatory, interoperability, and human-factors work.
- Roadmap from single-node showcase to retrospective evaluation and controlled go/no-go decisions.

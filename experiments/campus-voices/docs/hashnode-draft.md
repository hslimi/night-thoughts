Silent participation is a familiar university problem. A student may have done the reading, formed an idea, and still feel that speaking in a seminar carries too much social risk. Once the silence becomes a habit, waiting for the perfect contribution only makes the first sentence harder.

I wanted to experiment with a smaller question: could an always-on Mac mini provide a private place to rehearse that first contribution without recording a voice or turning practice into a score?

The result is **Campus Voices**, a five-minute, voice-first speaking lab. It has a consent notice, a pre-session confidence check-in, a simulated seminar partner, five optional participation goals, an end-session control, supportive feedback, a post-session check-in, and a delete-local-data button.

It is also deliberately limited. This experiment is a **scripted prototype**, not a Dessa integration, not a real-time speech-to-speech system, and not a student study. No learning outcome was measured.

![Campus Voices landing screen with the My First Seminar Contribution scenario, consent, confidence check-in, and five participation goals](https://cdn.hashnode.com/uploads/gql/6a92730f9a9aa7f72e74fdf4/040d520d-19d7-4048-917b-56480fbd293b.png)

_The production build running on 127.0.0.1:3000. All interactions shown are synthetic demonstrations._

## The Campus Voices scenario

The scenario is called **“My First Seminar Contribution.”** The participant speaks aloud to Sam, a simulated partner whose prompts come from a local script. The browser does not request microphone access. It cannot hear or transcribe the response; it only displays the next prompt and records the goals the participant chooses to mark as explored.

The five goals offer different ways into a conversation:

1. Make an opening contribution.
2. Explain your reasoning.
3. Ask a clarifying question.
4. Build on a peer’s idea.
5. Respond to a follow-up.

This distinction matters to me. Participation is not only delivering a polished answer. A question, an example, or one more turn after a follow-up can be a meaningful place to begin.

The goals are self-reflection, not grading. The participant can explore them in any order and can end the session early. The feedback screen does not assign a participation score or infer academic ability.

![Active Campus Voices practice screen with Sam's scripted prompts, a five-minute timer, five participation goals, and an end-session button](https://cdn.hashnode.com/uploads/gql/6a92730f9a9aa7f72e74fdf4/525ce306-21e7-4bc4-b8a4-8b54994c34d0.png)

_The active seminar-practice interface. The timer and partner script work without capturing audio._

## Hardware and the existing foundation

The reference machine is my always-on **Mac mini M5 with 48 GB of memory**. Campus Voices joins the foundation I had already built there:

- MLX and oMLX for local model inference;
- QwenPaw as part of the broader local-AI environment;
- Caddy as the reverse proxy;
- Cloudflare Tunnel for public HTTPS routes.

The application does not need a GPU server or a hosted speech API. The browser client is built with Vite and TypeScript, and a small Express server serves the production assets and feedback endpoint.

The original foundation guide is [Complete Guide: Always-On Mac Server with MLX, oMLX & QwenPaw](https://nightthoughts.me/complete-guide-always-on-mac-server-with-mlx-omlx-qwenpaw). This experiment adds an application route; it does not replace that server setup.

## Architecture

The request path is intentionally short:

- The **browser** renders the scenario and stores only consent, confidence ratings, goal identifiers, and a session count in localStorage.
- The **Campus Voices server** serves the client and accepts anonymous practice metrics for feedback.
- A **VoiceProvider interface** defines how a provider starts, emits a partner prompt, advances, and stops.
- The **scripted provider** implements that interface with fixed Sam prompts. It is the provider used throughout this experiment.
- A **Dessa provider** exists only as a disabled future implementation. It throws if used without real access and is never selected by the application.
- The server can call a **local oMLX endpoint** on `127.0.0.1:8000`. The API key exists only in the server process.
- For public access, **Cloudflare Tunnel** connects to **Caddy**, which forwards only the Campus Voices hostname to `127.0.0.1:3000`.

There is no public oMLX route in this design. There is also no session database. The application server does not retain practice sessions.

For oMLX feedback, the model receives only starting confidence, the count of self-reported goals explored, and elapsed seconds. It receives no goal text, audio, transcript, name, or free-form student response. If configuration is missing, the request fails, or the model output conflicts with the privacy and measurement rules, the server returns a clearly labelled scripted reflection instead.

## Building the prototype

The important files are small enough to inspect directly:

- `app/src/content.ts` defines the five goals, five-minute duration, and Sam’s prompts.
- `app/src/providers/voice-provider.ts` is the replaceable provider contract.
- `app/src/providers/scripted-provider.ts` implements this experiment’s simulated partner.
- `app/src/providers/dessa-provider.ts` keeps Dessa explicitly disabled.
- `app/src/main.ts` connects consent, the timer, goals, feedback, and deletion.
- `app/src/session.ts` validates and bounds the local-only state.
- `server/feedback.ts` validates anonymous metrics, calls oMLX server-side, checks the returned text, and supplies the scripted fallback.
- `server/app.ts` adds the API, production security headers, and static serving.

Why use an interface for such a simple script? Because I did not want the session flow to depend on a particular speech vendor. A future real-time provider will need to satisfy the same lifecycle and privacy requirements without forcing a rewrite of consent, timing, goals, or local deletion. That is an architectural seam, not a claim that the future provider already works.

The feedback guard also matters. During testing, a small local model produced text that suggested recording the next session. I rejected that output rather than treating every model response as acceptable. The final implementation rejects recording and transcription suggestions, claims to have heard the speaker, and unsupported statements about progress or learning.

## Running it locally

Clone the repository and install with the included npm lockfile:

```bash
git clone https://github.com/hslimi/night-thoughts.git
cd night-thoughts/experiments/campus-voices
npm ci
cp .env.example .env
```

Keep the server bound to localhost:

```dotenv
HOST=127.0.0.1
PORT=3000
OMLX_BASE_URL=http://localhost:8000/v1
OMLX_MODEL=replace-with-your-local-model
OMLX_API_KEY=replace-locally
```

Replace the oMLX values only in the ignored local `.env`. To see which models the existing endpoint offers, query it locally without printing the key:

```bash
curl --fail --silent --show-error \
  -H "Authorization: Bearer ${OMLX_API_KEY}" \
  http://127.0.0.1:8000/v1/models
```

Run the checks and production build:

```bash
npm run format:check
npm run lint
npm run typecheck
npm test
npx playwright install chromium
npm run test:e2e
npm run build
node scripts/verify-static.mjs
npm start
```

Then open `http://127.0.0.1:3000`. The browser tests exercise the complete synthetic scenario, including the automatic five-minute ending and local-data deletion. The static check rejects server credential names and browser speech-capture APIs in the built client.

## Exposing campusvoices.nightthoughts.dev

The intended public route is:

```text
HTTPS → Cloudflare Tunnel → Caddy on 127.0.0.1:9080
      → Campus Voices on 127.0.0.1:3000
```

Add only this block to the existing Caddyfile, preserving every unrelated route:

```caddy
http://campusvoices.nightthoughts.dev {
    encode zstd gzip
    reverse_proxy 127.0.0.1:3000
}
```

Validate before restarting Caddy:

```bash
caddy validate --config /path/to/Caddyfile
```

In the existing tunnel configuration, place the application rule before the final catch-all:

```yaml
- hostname: campusvoices.nightthoughts.dev
  service: http://127.0.0.1:9080
```

Validate the tunnel configuration, restart the existing service, and add the DNS route with the existing tunnel name:

```bash
cloudflared tunnel route dns EXISTING_TUNNEL_NAME campusvoices.nightthoughts.dev
```

Finally verify `https://campusvoices.nightthoughts.dev/api/health` and repeat the synthetic browser scenario over HTTPS. A future provider that requests microphone access needs HTTPS outside localhost, and permission will be specific to that origin. The current scripted provider does not request microphone permission.

**Deployment checkpoint for this draft:** the sanitized Caddy block validated successfully, but applying the block to the root-owned live Caddyfile requires an administrator session. That access was unavailable in this run, so I did not change Caddy or Cloudflare and I am not claiming that the public HTTPS check passed. The public screenshot will be added only after that route works.

![Terminal showing caddy validate for the sanitized Campus Voices configuration and the result Valid configuration](https://cdn.hashnode.com/uploads/gql/6a92730f9a9aa7f72e74fdf4/3261b78d-8b7e-4597-be2b-1d3bd6d7b721.png)

_The sanitized Caddy example validates. This is not evidence that the live public route has been deployed._

## Privacy and safety

The default data boundary is more important than the interface:

- **No recordings or transcripts.** The scripted provider uses no microphone or cloud speech service.
- **No public oMLX exposure.** The model endpoint remains on localhost.
- **No browser-accessible API keys.** Only the Express server reads the oMLX credential.
- **No accent, emotion, or academic-ability scoring.** Confidence is a self-report, not an inference.
- **Local deletion.** The privacy dialog and feedback screen remove the application’s localStorage key.
- **Restricted development access.** Cloudflare Access is recommended before exposing an evolving prototype.

![Campus Voices privacy dialog explaining local browser storage, anonymous practice metrics, and the delete-local-data control](https://cdn.hashnode.com/uploads/gql/6a92730f9a9aa7f72e74fdf4/ed3f2289-4ab8-44ed-bac4-eb67f9d38f50.png)

_The local-data controls. The dialog states exactly what is and is not collected._

This is not a student research deployment. Any real pilot needs institutional consent, ethics review, an appropriate data-management plan, and a fresh accessibility and security assessment.

## Results and limitations

The checks that passed in this run were:

- Prettier formatting and ESLint;
- TypeScript checks for browser, tests, and server;
- 15 unit tests across local state, providers, feedback validation, and the server API;
- three Playwright tests covering the full scenario, automatic five-minute ending, privacy controls, and credential non-disclosure;
- the production Vite and server builds;
- a browser-bundle check for credential names and speech-capture API references;
- production listening on `127.0.0.1:3000`;
- a real local oMLX feedback request returning `source: omlx` with the validated output boundary;
- validation of the sanitized Caddy example.

The live Caddy change, Cloudflare change, public DNS resolution, and public HTTPS screenshot remain unverified for the reason described above.

Everything else still needs to be read as prototype evidence. The provider is scripted. Dessa is disabled. The feedback is supportive text, not an evaluation. Self-reported confidence before and after a session is not a validated learning measure. No student participants were recruited, and no real student data was collected.

![Campus Voices feedback screen showing synthetic goals, three minutes of practice, local oMLX supportive feedback, and a post-session confidence control](https://cdn.hashnode.com/uploads/gql/6a92730f9a9aa7f72e74fdf4/fe65620f-b23f-4f24-b01a-22ba8f6af1cb.png)

_A synthetic feedback screen after a three-minute demonstration. It does not represent a research result._

## What comes next

The next useful step is a real-time audio provider behind the existing interface, not a more elaborate script. That would bring the difficult engineering questions with it: round-trip latency, interruptions, partial responses, microphone permissions, failure recovery, and whether any audio buffer is retained.

I would also want to test with screen readers, keyboard-only interaction, different speaking styles, and accessibility specialists before treating the interaction as inclusive. Only after those checks would a small, ethics-approved pilot make sense.

The goal would not be to make students sound alike. It would be to offer a private rehearsal space where a first contribution feels more possible.

## Source code

The complete experiment, lockfile, tests, sanitized infrastructure examples, screenshots, and reproduction guide are available at:

[github.com/hslimi/night-thoughts/tree/main/experiments/campus-voices](https://github.com/hslimi/night-thoughts/tree/main/experiments/campus-voices)

The local setup guide is in `docs/setup-guide.md`. The article and application will remain explicitly separate from any future student research deployment.

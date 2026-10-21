---
title: "Onyx: The Open-Source AI Assistant That Keeps Company Data at Home"
datePublished: 2026-10-21T15:01:52.286Z
cuid: cmvi8q6mw000e09jwcxbm025e
slug: onyx-the-open-source-ai-assistant-that-keeps-company-data-at-home
cover: https://cdn.hashnode.com/uploads/covers/6a92730f9a9aa7f72e74fdf4/ada7062c-6e3f-48c9-abb4-1416a26e62eb.jpg
tags: ai, docker, opensource, privacy, self-hosted, rag

---

Most companies have information scattered across Google Drive, Slack, Jira, Confluence, and dozens of other tools. When an employee needs an answer, they spend hours searching. AI can help, but sending internal company data to a closed cloud service is not an option for many organizations.

**Onyx** (formerly Danswer) is an open-source, self-hosted AI assistant that connects to a company’s apps, searches them, and answers questions. Because it is open source, anyone can inspect the code. Because it is self-hosted, the company retains full custody of its data. The project lives on GitHub at **github.com/onyx-dot-app/onyx**. The community edition is free under the MIT license, covering chat, RAG, agents, and actions; a separate enterprise edition adds SSO, permission sync, white-labeling, and analytics.

### The Short Story Behind Onyx

Onyx started in 2023 when two software engineers, **Chris Weaver** and **Yuhong Sun**, set out to solve a problem they kept encountering: new employees simply could not find the information they needed. After two earlier startup attempts that didn't work out, they released an early version under the name **Danswer**. Companies like the fintech firm **Ramp** soon found the project and asked to pay for a product that was completely free. That demand led them to turn the open-source project into a company, backed by **Y Combinator** and a **$10 million seed round** from Khosla Ventures and First Round Capital.

### Real Examples of How Companies Use It

Onyx is not a general-purpose chatbot. It is a search and research tool that works inside a company’s existing tools and respects existing access rules.

**Example 1: Customer support.** A support agent gets a complex billing question. Instead of digging through old Slack threads, Jira tickets, and PDFs, they ask Onyx. It searches connected tools at once and returns an answer with links to the source. If that agent does not have permission to see a private engineering ticket, Onyx will not surface it.

**Example 2: New employees.** Questions like “How many vacation days do I get?” or “What is the remote work policy?” can be answered instantly. Onyx finds the relevant HR document in Google Drive and gives the answer, without waiting for an email reply.

**Example 3: Sales teams.** Onyx’s AI research agent can handle multi-step questions. If someone asks, “How did we close this deal so quickly?”, the agent runs parallel searches across Salesforce, Gong, email, and Slack, combines the results, and gives a summary—rather than returning a single keyword match.

### Why Self-Hosting Matters

Onyx can be deployed on a company’s own servers and connects to more than 40 internal data sources including Salesforce, GitHub, Google Drive, and Confluence. 

- **Data control and custody.** For healthcare, finance, and defense organizations, keeping sensitive data on-premises is often a hard requirement. With self-hosting, the company retains full control and legal custody of its data. Onyx is currently deployed at **Thales Group**, a defense company, and at **Netflix** for all 14,000+ employees.
- **Cost and model control.** Companies choose their own AI model—commercial options like OpenAI or Anthropic, or local models via Ollama—and pay for the server they run it on, not per seat.
- **No vendor lock-in.** If a company stops using Onyx, the code and data remain on its own infrastructure.

*Note on deployment:* While a basic evaluation instance can be spun up in about 30 minutes using Docker, a production deployment at enterprise scale requires proper infrastructure, ongoing maintenance, and security patching.

### The Community and Business Model

As of recent reviews, Onyx has roughly **32,000 stars on GitHub** and has seen over 250 releases. The community edition is MIT-licensed, which means developers can test it, fix bugs, and add features without asking permission.

The business model is open-core: the free community edition drives adoption. Organizations that need stricter security and management tools can upgrade to the **Business tier (starting at $20 per user per month)** or the Enterprise tier. These paid versions include critical features like **permission sync** (ensuring Onyx respects source-system access rules dynamically), single sign-on (SSO), and white-labeling. Because the free version is genuinely usable, companies can try it without a long sales process.

### The Caveats: What Self-Hosting Really Requires

While self-hosting solves the problem of data leaving your servers, it is not a magic wand. Running Onyx in a real company comes with responsibilities:

- **Privacy is a setup task, not a guarantee.** Onyx connects to your apps and respects their permissions, but *you* must configure those permissions correctly. If the system that syncs user access breaks, Onyx might show data to the wrong people. You still need to monitor who has access to what.
- **AI makes mistakes.** Onyx uses large language models (LLMs), which can confidently give wrong answers. If an employee asks about a legal policy or a financial figure, Onyx might misread a document. Human oversight and a feedback loop (letting users report bad answers) are necessary, especially for high-stakes topics.
- **You are the IT department.** When you self-host, the company is responsible for keeping the servers running, applying security patches, and scaling the hardware as more employees use it. This requires a technical team or a managed service provider.
- **Regulatory compliance is still your job.** Installing Onyx on your own servers does not automatically make you GDPR or HIPAA compliant. You still need legal reviews, audit logs, and data retention policies to ensure the AI does not accidentally store or process sensitive information in ways the law prohibits.

### The Bottom Line

Onyx is a practical tool for a specific problem: company knowledge is scattered, and employees need a private, permission-aware way to search it. It does not promise to replace every AI product. It promises to keep data on your servers, work with the tools you already use, and let you choose your own model. That straightforward approach—paired with careful setup and human oversight—is why thousands of developers and real companies are using it today.

**GitHub:** https://github.com/onyx-dot-app/onyx
**Website:** https://onyx.app

---
*If you care about open-source infrastructure, data privacy, or practical AI for the workplace, consider following or sponsoring the project.*
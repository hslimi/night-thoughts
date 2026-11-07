---
title: "Built to Leave: Vendor vs. In-House, AI's Two Races and the Sovereignty Illusion"
seoTitle: "Built to Leave: Cloud Dependency, AI and Sovereignty"
seoDescription: "A three-part essay on build vs buy in finance, AI's twin security and competitive races, and why cloud sovereignty is harder than it looks."
datePublished: 2026-10-02T13:37:43.359Z
cuid: cmur0cs6e000006p081wi6gqf
slug: the-old-trade-off-vendor-vs-in-house-before-ai-changed-the-rules
cover: https://cdn.hashnode.com/uploads/covers/6a92730f9a9aa7f72e74fdf4/2a6f1576-3f47-4503-a1fe-f38d0b0503ee.jpg
tags: ai, vendor, finance, public-cloud

---

*Built to Leave, in one essay: cloud dependency, sovereignty and the architecture that makes exit possible. Part 1 covers the build-vs-buy trade-off that predates AI. Part 2 covers the two races AI forces on financial institutions at once: security and competitiveness. Part 3 covers the sovereignty illusion and what companies can actually do about it. Series page: [nightthoughts.me/series/build-to-leave](https://nightthoughts.me/series/build-to-leave)*

---

## Part 1 — The Old Trade-Off: Vendor vs. In-House, Before AI Changed the Rules

Long before anyone in finance was talking about AI, institutions were already wrestling with one of the oldest questions in enterprise technology: build it yourself, or buy it from someone else. It's a decision every bank, insurer, and financial services firm has made repeatedly, across decades, for every new capability that came along — core banking systems, trading platforms, risk engines, data infrastructure. The technology changed. The underlying dilemma didn't.

This article isn't about AI yet. It's about understanding the trade-off as it existed before AI entered the picture — because you can't understand how AI is reshaping the game until you understand the board it's being played on.

### A brief chronology

Financial institutions have swung between these two poles for a long time, and rarely by pure technical logic — often by cost pressure, regulation, or the scars of a previous decision gone wrong.

In earlier decades, many institutions built almost everything in-house, out of necessity more than preference — the vendor ecosystem for specialized financial technology simply didn't exist yet. Core systems were custom, maintained by large internal IT departments, because there was no market offering an alternative.

As the vendor landscape matured, the pendulum swung toward buying. Specialized providers emerged for almost every function — trading systems, compliance tooling, payment processing, data feeds — and outsourcing that work became the default, because building it yourself no longer made economic sense against a mature, specialized alternative.

More recently, the pendulum has been swinging back, at least partially. Institutions that outsourced heavily started reckoning with the risks of that dependency, and many began reinvesting in in-house engineering capability — not to replace vendors entirely, but to regain control over what they saw as strategically important.

Neither swing was permanent, and neither was universally correct. What's stayed constant is the underlying trade-off itself.

### The case for the vendor

Buying from an external provider has always come with a clear pitch: **you get expertise and speed without having to build the capability yourself.**

*   **Cost predictability (at least on paper).** You pay for a service rather than building and maintaining the underlying capability, converting a large fixed investment into a more variable one.
    
*   **Specialized expertise.** Vendors often have deep, focused expertise in a narrow domain that would take years for an internal team to replicate.
    
*   **Faster time to market.** A mature vendor product can often be deployed faster than a custom-built equivalent, because much of the engineering work is already done.
    
*   **Shared risk, in theory.** SLAs and contracts create an expectation that the vendor shares responsibility for uptime, security, and support.
    

But this pitch has always come with a quieter set of liabilities, ones that only become visible over time:

*   **You don't control the roadmap.** The vendor's priorities are not necessarily your priorities, and you may find yourself waiting on features, fixes, or changes that matter to you but not to their broader customer base.
    
*   **Dependency risk compounds.** The longer you rely on a vendor, the more expensive and disruptive it becomes to leave — even if the relationship deteriorates.
    
*   **The vendor can fail you in ways outside your control.** Contract terms can change unilaterally once switching costs are high enough. Vendors can be acquired, restructured, or go bankrupt, taking your roadmap down with them. A security breach or outage on their side becomes an incident on yours, regardless of whose code was vulnerable — regulators such as FINRA have specifically flagged the rise in cyberattacks and outages at third-party vendors as a risk that can ripple across large numbers of firms at once ([FINRA](https://www.finra.org/rules-guidance/guidance/reports/2025-finra-annual-regulatory-oversight-report/third-party-risk)). And increasingly, geopolitical shifts — sanctions, export controls, data residency requirements — can sever access to a vendor's service almost overnight, regardless of what the contract says.
    
*   **You become the auditor, not the owner.** Choosing a vendor doesn't remove your responsibility — regulators make that explicit in financial services. Outsourcing a function does not outsource the accountability for it: if a critical provider fails, the institution's own customers feel the consequences and its own regulator expects a response, including formal incident reporting where thresholds are met ([calQrisk](https://www.calqrisk.com/resources/insights/outsourcing-and-third-party-risk-management-for-financial-firms)). The EU's Digital Operational Resilience Act (DORA), in force since January 2025, codifies exactly this: it gives supervisors the power to designate systemically important ICT and cloud providers as "critical third-party providers" subject to direct oversight, precisely because of the concentration risk created when many institutions lean on the same few providers ([PIFS International](https://www.pifsinternational.org/cloud-adoption-in-the-financial-sector-and-concentration-risk/); [Bristows](https://inquisitiveminds.bristows.com/post/102lqkb/aws-us-east-1-incident-regulators-concentrate-on-concentration-risk)). Canada's OSFI guidance is just as direct, advising regulated institutions to consider strategies such as multi-cloud design specifically to mitigate cloud-provider concentration risk ([OSFI](https://www.osfi-bsif.gc.ca/en/guidance/guidance-library/third-party-risk-management-guideline)). That's the real substance behind "you become the auditor" — ongoing due diligence, SLA monitoring, security assessments, and resisting the temptation to let any single vendor become a single point of failure.
    

### The case for in-house

Building internally has always promised the opposite: **control, at a price.**

*   **Full ownership of the stack.** No dependency on a third party's roadmap, pricing decisions, or continued existence.
    
*   **Institutional knowledge stays inside the company**, compounding over time rather than walking out the door when a vendor contract ends.
    
*   **Tighter alignment with regulatory and compliance requirements**, since governance sits entirely within the institution's own control rather than being negotiated through a vendor relationship.
    
*   **Faster internal feedback loops**, at least once a team is mature — the people who build a system are also the ones maintaining and evolving it, without a vendor relationship as an intermediary.
    

And the costs, while less visible than a vendor invoice, are just as real:

*   **Fixed cost that doesn't scale down.** Infrastructure and talent are ongoing commitments, whether the system is running at 20% capacity or 90%.
    
*   **Slower delivery, particularly in regulated environments.** Every internal change typically passes through governance, audit trail requirements, and compliance review — overhead that a mature vendor product may have already absorbed into its design and certifications.
    
*   **Mission drift.** For a financial institution, IT is not the core business. The more capability is brought in-house, the more the institution is, in effect, also becoming a software organization — competing for technical talent, carrying technical debt, and needing a level of engineering maturity that doesn't come naturally to a business built around finance, not software.
    
*   **Self-auditing is still auditing** — **and it's easier to under-invest in.** Owning the stack doesn't remove the need for rigorous internal controls; it just moves that function inside the institution's own walls, where there's no external contract forcing the discipline. In-house risk tends to fail quietly, through neglect, while vendor risk tends to fail loudly, through breach disclosures and contract disputes — and that asymmetry in visibility often shapes the debate more than the actual underlying risk does.
    
*   **The operational headache no slide deck shows.** Owning your IT end-to-end means owning problems that have nothing to do with writing good software. Running global operations means organizing a genuine follow-the-sun strategy — coverage across time zones, handovers that don't lose context, incident response that works at 3 a.m. somewhere no matter what. It means spreading knowledge across a distributed workforce rather than concentrating it in a single team, which is harder to do well than it sounds. And paradoxically, the more IT you own, the closer IT has to sit to the business — which means growing the very "bigger IT" organization that the mission-drift argument warns against in the first place.
    
*   **Data center provisioning is its own discipline.** Standing up and running physical infrastructure — capacity planning, power, cooling, hardware refresh cycles, physical security — is a specialized competency in itself, largely unrelated to financial services. Institutions that own this end-to-end are committing real, ongoing effort to keep SLAs at the level the business requires, effort that has nothing to do with banking or finance and everything to do with running a data center well.
    
*   **Hosting costs that only go one direction.** The cost of maintaining and upgrading data center infrastructure tends to climb over time, not fall. Construction costs per megawatt of IT load have risen sharply as demand for power-hungry, high-density facilities has surged, with electrical infrastructure now consuming close to half of total project budgets ([Terrapin CG](https://terrapincg.com/news/average-cost-to-build-a-data-center-in-the-usa); [iRecruit](https://www.irecruit.co/insights/data-center-construction-cost-trends-2026)). Power itself has become the binding constraint: grid operators and energy researchers point to data center demand as a meaningful driver of rising electricity costs in several markets ([Fortune](https://fortune.com/2026/07/26/data-centers-electricity-costs-cheaper-7billion-buildout-ai-demand/)). Running infrastructure at the resilience level financial regulators expect isn't cheap, and the trend line isn't moving in the direction that makes self-hosting easier over time.
    
*   **Resiliency requirements are escalating faster than most in-house setups can absorb.** Geopolitical instability and worsening climate conditions — more frequent flooding, wildfires, earthquakes, and extreme weather events — are pushing infrastructure resilience requirements toward multi-region, geographically diversified setups almost as a baseline expectation now, not a best practice for the ambitious. This isn't a theoretical concern: one global analysis of nearly 9,000 data centers found that a meaningful share already sit in locations facing high or moderate physical climate risk, with several major hubs projected to see a large proportion of their facilities exposed by 2050 ([DCD](https://www.datacenterdynamics.com/en/news/climate-threats-to-data-centers-set-to-surge-report/); [XDI](https://xdi.systems/news/global-data-centres-face-rising-climate-risks-xdi-report-warns-landmark-analysis-of-nearly-9000-sites-reveals-escalating-threat-to-digital-infrastructure)). A separate analysis of global data center markets put the share of capacity exposed to acute climate hazards — flooding, extreme wind, wildfire — at close to four in five facilities worldwide ([CNBC](https://www.cnbc.com/2026/06/18/data-center-climate-change-study.html)). Meeting a rising resilience bar in-house means duplicating infrastructure across regions, at a cost and complexity that grows with every added region. At a certain point, this pressure alone pushes institutions to conclude that running physical infrastructure at that level of resiliency is better delegated to an organization for whom that *is* the core business — which is precisely the case public cloud providers make.
    

### The speed trap: how both paths lead to the same mess

There's a dimension to this trade-off that doesn't show up in cost comparisons or risk matrices, but that anyone who has actually shipped software in a bank will recognize immediately: speed pressure distorts both paths, and it tends to distort them toward the same outcome.

When the business sees an opportunity, the instinct is to move before competitors do. On the in-house side, that pressure produces what I'd call **commando mode** — or sniper mode: build exactly what's needed, nothing more, and move fast. No time for the full picture. No time to future-proof. Just enough to seize the opportunity, now, while it's there. And for day one, this works. It's often the *right* call — a mature, fully governed build process would have missed the window entirely.

The problem is what happens next. As soon as that commando-mode build reaches production and the business succeeds, the very success creates pressure the system was never built to absorb. It doesn't scale. Clients want more than the minimal version can deliver. The business struggles to understand why something that clearly works can't simply be extended — surely if it does *this*, it can do *that* too? And underneath, the parts that were skipped in the rush — proper security, authentication, resilience — are exactly the parts that are hardest and most expensive to retrofit once real usage and real data are flowing through the system.

The vendor path isn't immune to its own version of this trap, just from a different direction. Getting real value out of a vendor platform — configuring it properly, building the features specific to your business — requires expertise, and that expertise is often scarce and expensive. Institutions frequently end up dependent on a small number of specialists who understand the vendor's tool deeply, and just as often end up building a growing constellation of **satellite applications** around the vendor platform to bridge the gaps it doesn't cover natively. Ironically, by the time all of that is stitched together, time to market on the vendor path can end up *slower* than a commando-mode in-house build — the very speed advantage vendors are supposed to offer gets eaten by integration and customization overhead.

Here's the uncomfortable convergence: **whichever path you take, the default outcome, without deliberate intervention, is the same** — a sprawling landscape of small applications in production, built under time pressure, neither scalable nor properly secured, each one requiring real ongoing effort, spread across teams worldwide, just to keep it up and running.

This is where I think the real discipline lives — not in choosing build or buy correctly in the abstract, but in resisting the urge to let either path run on pure speed indefinitely. At some point, an institution has to deliberately slow down: organize what's been built, structure it properly, size the actual opportunity rather than the emergency that created it, and identify which of these applications are mature and important enough to deserve real investment — and which should be retired, consolidated, or never should have reached production in their current form in the first place.

### Neither side is "safe"

What's striking, looking back across this history, is how often the debate gets framed as if one side is the "risky" choice and the other is the "safe" one. It never has been. Buying and building simply distribute risk differently — one concentrates it in a third-party relationship you have to actively manage, the other concentrates it inside your own walls, where it's your discipline alone keeping it in check.

The institutions that navigated this well weren't the ones that picked a permanent side. They were the ones that got specific: deciding deliberately which capabilities were core enough to own directly regardless of cost, and which were commodity enough that well-managed vendor risk was the better bet — and revisiting that decision as circumstances changed, rather than defaulting to "how we've always done it."

That balance held, imperfectly but functionally, for decades. But something is changing the terrain underneath it — and not gradually, the way most technology shifts do.

Part of the pressure is infrastructural: resiliency expectations are rising faster than most institutions can build for on their own, quietly pushing even committed in-house organizations toward providers whose entire business is running resilient infrastructure at global scale. Part of it is a discipline problem that predates any of this — the speed trap that fills production with small, fragile applications regardless of which path built them. And part of it is genuinely new, arriving from two directions at once.

One is defensive: the attacker on the other side of the wall is no longer just a person trying a few things and giving up when they fail. The other is competitive, and arguably the more urgent of the two: institutions that learn to use AI well are already starting to produce things faster, at lower cost, with better products, than those that don't. That's not a security question at all — it's a market-share question. An institution can have flawless security and still lose ground simply by being slower and more expensive than a competitor who figured out how to fold AI into their delivery cycle.

Both pressures point toward the same infrastructure — the data, compute, and platforms that make AI viable at scale — but for very different reasons. One is about not losing what you have. The other is about not falling behind. A few open questions to sit with before the next piece:

*   If resiliency and infrastructure ownership are already pushing institutions toward the cloud on their own, what happens when both defending against an always-on attacker *and* keeping up with AI-native competitors make that pull even harder to resist?
    
*   Is the "slow down and get organized" discipline this article calls for even compatible with a competitive environment where the institutions moving fastest with AI are also the ones pulling ahead?
    
*   And if the answer increasingly runs through public cloud — whose infrastructure is it, really, and what does that mean for an institution's independence when both its security and its competitiveness depend on it?
    

*What happens to this trade-off when infrastructure itself becomes too demanding to own alone, discipline becomes harder to enforce under competitive pressure, the attacker never sleeps, and standing still means falling behind? That's where we go next.*

* * *

#### References

*   PIFS International, ["Cloud Adoption in the Financial Sector and Concentration Risk"](https://www.pifsinternational.org/cloud-adoption-in-the-financial-sector-and-concentration-risk/)
    
*   Office of the Superintendent of Financial Institutions (OSFI), ["Third-Party Risk Management Guideline"](https://www.osfi-bsif.gc.ca/en/guidance/guidance-library/third-party-risk-management-guideline)
    
*   Bristows, ["AWS US-EAST-1 incident: regulators concentrate on concentration risk"](https://inquisitiveminds.bristows.com/post/102lqkb/aws-us-east-1-incident-regulators-concentrate-on-concentration-risk)
    
*   calQrisk, ["Outsourcing and Third-Party Risk Management for Financial Firms"](https://www.calqrisk.com/resources/insights/outsourcing-and-third-party-risk-management-for-financial-firms)
    
*   FINRA, ["Third-Party Risk Landscape," 2025 Annual Regulatory Oversight Report](https://www.finra.org/rules-guidance/guidance/reports/2025-finra-annual-regulatory-oversight-report/third-party-risk)
    
*   Data Center Dynamics, ["Climate threats to data centers set to surge"](https://www.datacenterdynamics.com/en/news/climate-threats-to-data-centers-set-to-surge-report/)
    
*   XDI, ["Global data centres face rising climate risks"](https://xdi.systems/news/global-data-centres-face-rising-climate-risks-xdi-report-warns-landmark-analysis-of-nearly-9000-sites-reveals-escalating-threat-to-digital-infrastructure/)
    
*   CNBC, ["Data center climate change study"](https://www.cnbc.com/2026/06/18/data-center-climate-change-study.html)
    
*   Terrapin CG, ["Average Cost to Build a Data Center in the USA"](https://terrapincg.com/news/average-cost-to-build-a-data-center-in-the-usa)
    
*   iRecruit, ["Data Center Construction Cost Trends 2026"](https://www.irecruit.co/insights/data-center-construction-cost-trends-2026)
    
*   Fortune, ["Data centers and electricity costs"](https://fortune.com/2026/07/26/data-centers-electricity-costs-cheaper-7billion-buildout-ai-demand/)

---

## Part 2 — Two Races at Once: Why AI Is Both a Security Emergency and a Competitive One

Part 1 ended with two forces pulling financial institutions toward the same infrastructure, for very different reasons: one defensive, one competitive. This piece looks at what that means once both land on the same roadmap at the same time, based on what I've seen in cloud transformation work, kept at the general level rather than tied to any one employer.

### Security is not one bank's problem

Security in a bank is never negotiable. A serious breach doesn't stay contained — banks are wired into each other, and a failure at one institution can ripple into all of them. That's why the sector's response is increasingly collective, not institution by institution. Project Glasswing, launched by Anthropic in April 2026, brings major banks and hyperscalers together — JPMorgan, AWS, Google, Microsoft, Palo Alto Networks — to jointly use AI to find and fix vulnerabilities before attackers do, and by June 2026 it had expanded to roughly 150 more partners across 15+ countries.

The urgency behind that effort just became a lot more concrete. On September 3, 2026, OpenAI released GPT-6 Astra — the first commercial AI model to reach OpenAI's own "Critical" threshold for cybersecurity capability. According to OpenAI's system card, Astra can find previously unknown security flaws and develop new ways to exploit them across well-protected systems, without a person guiding each step. In pre-release testing it discovered two zero-day vulnerabilities on its own. This is no longer hypothetical. As of this month, that capability exists commercially, under gated access. Fighting it requires AI-capable defense, alongside the discipline that comes with it: zero trust as a default, continuous scanning across binaries, source code, third-party libraries, and internal systems, and relentless tracking of vulnerabilities before they can be weaponized.

### The other pressure

Security isn't the only force reshaping the roadmap. A second pressure is building in parallel, and it decides who's still standing in five years: competitiveness. There are two different things "AI" can mean here. One is tooling — copilots inside email, code, presentations — which makes existing work faster without changing what the business does. The other is AI as a business function: pricing, credit scoring, fraud detection — AI that changes the product itself. That second category is what actually moves the competitive needle.

Institutions that adopt it early are already pulling ahead on cost and performance; slower movers risk a cost base they can't compete with. Multiple surveys show banks now ranking cost reduction and productivity ahead of security as reasons to invest in AI. Even inside institutions that treat security as non-negotiable, the case for AI is increasingly built around staying competitive, not just staying safe.

### Where I've seen this actually play out

The technology was rarely the hardest part. Two things running in parallel were.

The first is applying real security discipline against a technology landscape that, in most institutions I've seen, was never built with that discipline in mind. You can't zero-trust your way through hundreds of small, loosely documented applications overnight, especially against an adversary that can now automate vulnerability discovery at machine speed. Every one of those applications is its own scanning target, its own audit trail, its own zero-day exposure to track. Multiply a hard problem by a fragmented estate, and it becomes close to unmanageable regardless of budget.

The second is organizational: getting an institution to agree, in practice and not just in principle, on what gets funded first when security and AI competitiveness are both labeled the top priority. They compete for the same architects, the same budget cycle, the same production windows. That tension doesn't resolve through better slogans. It resolves by removing the reason it exists.

### The fix nobody wants to do first

Most institutions aren't failing to prioritize security or competitiveness. They're trying to do both against an application landscape that should never have gotten this fragmented. Every small, tactically-built application — built to hit a deadline, wrapped around

---

## Part 3 — The Sovereignty Illusion: What Companies Get Wrong About Cloud Independence

In Part 1, I looked at the oldest trade-off in enterprise technology: build it yourself, or buy it from someone else. In Part 2, I looked at how two forces—defensive security and offensive competitiveness—are pushing financial institutions toward the same infrastructure at the same time. This chapter looks at the foundation both of those forces run on, and the uncomfortable question underneath it: **whose cloud is it, really?**

There's a phrase that captures the core misunderstanding I want to unpack here: *"Your data, their laws."* It sounds provocative, maybe even alarmist. But for a European company storing data with a US-headquartered cloud provider, it is a literal description of the legal reality. The US CLOUD Act and FISA allow US authorities to compel US-incorporated companies to hand over data—regardless of where that data is physically stored. A server in Frankfurt does not put that data beyond the reach of US law if the company operating it is subject to US jurisdiction.

That's the sovereignty illusion. For years, "sovereign cloud" has been sold to European companies as a matter of data residency: keep the bits inside EU borders, and you've solved the problem. But jurisdiction follows the company, not the server. And as long as the parent company answers to another government's laws, "complete sovereignty" remains out of reach.

This matters most for Europe, where the gap between ambition and reality is widest. US hyperscalers control over 70% of the European cloud market. European providers hold around 15%, a share that has barely moved despite years of investment and political will. DORA has given European supervisors new powers over critical third-party providers, but oversight is not the same as alternatives. And the concentration risk isn't theoretical—the October 2025 AWS US-East-1 outage took down European banks, brokerages, and payment systems, a preview of what's at stake when the infrastructure you don't control fails.

For US or Chinese companies, this is rarely a live question—they operate under the same jurisdiction as their dominant cloud providers. For European companies, it is unavoidable. So what does "independence" actually mean when both your security posture and your competitive AI capability depend on infrastructure owned by someone else, operating under someone else's laws? That's the question this chapter sits with. It doesn't have a tidy answer—but the first step is naming the problem clearly: **your data, their laws.** Everything else follows from there.

---

### Why Public Cloud Is Non-Negotiable

Before getting into the risks, it's worth being honest about why European companies can't simply walk away from public cloud. The dependency isn't a failure of strategy; it's a rational response to three converging pressures.

**AI requires scale.** Generative AI has deepened dependency across three layers: specialized chips (Nvidia-dominated), foundation models (GPT, Gemini, Claude), and integrated AI platforms from hyperscalers. Building that stack in-house is not a realistic option for most companies. The compute requirements alone—training runs costing tens of millions, inference at scale requiring global distribution—put it out of reach for any institution whose core business is finance, not infrastructure.

**Resilience demands it.** Rising climate and geopolitical risks are pushing infrastructure resilience requirements toward multi-region, geographically diversified setups almost as a baseline expectation now, not a best practice for the ambitious. One global analysis of nearly 9,000 data centers found that a meaningful share already sit in locations facing high or moderate physical climate risk. A separate analysis put the share of capacity exposed to acute climate hazards—flooding, extreme wind, wildfire—at close to four in five facilities worldwide. Meeting that bar in-house means duplicating infrastructure across regions, at a cost and complexity that grows with every added region.

**Cost efficiency is real.** For years, US hyperscalers offered European companies unmatched scalability and cost efficiency. The pay-as-you-go model converts large fixed investments into variable costs. For institutions under margin pressure, that flexibility is not a luxury—it's a competitive necessity.

**Regulatory pressure cuts both ways.** DORA requires robust operational resilience, but it also acknowledges that cloud concentration is a systemic risk. The regulation gives supervisors new powers over critical third-party providers, but oversight is not the same as alternatives. A covered entity using a designated provider gets some assurance that the provider is being supervised, but the covered entity remains accountable for its own risk management.

The point is this: public cloud isn't a choice European companies can undo. The question is what that dependency actually costs—and whether the price is being measured honestly.

---

### The Risks: What Companies Are Actually Paying For

#### The Jurisdiction Trap

The US CLOUD Act and FISA allow US authorities to compel US-incorporated companies to hand over data regardless of where it's stored. This creates a direct conflict with GDPR and the EU's data protection framework. A server in Frankfurt is legally an American server. Data residency only answers where data sits, not who can be compelled to hand it over.

This isn't a theoretical concern. The CLOUD Act was designed precisely to resolve conflicts between US law enforcement demands and foreign data protection laws—and it resolves them in favor of US access. For a European company, that means the legal protections you've built around data residency can be overridden by a legal order you have no standing to contest.

#### Concentration Risk

According to the Dutch Authority for the Financial Markets (AFM) and De Nederlandsche Bank (DNB), the Dutch financial sector faces increasing systemic risks stemming from its growing reliance on a limited number of non-European IT service providers. The regulators caution that this dependency amplifies the risk of concentration and systemic disruption, where a failure at a single provider could impact large segments of the financial sector ([AFM & DNB, 2025](https://www.afm.nl/en/sector/actueel/2025/okt/pb-digitale-autonomie)).

More than 30% of significant EU institutions' total outsourcing budgets flow to just 10 providers. In 2025, 29% of major ICT incidents reported across the EU financial sector originated from third-party provider failures. The October 2025 AWS US-East-1 outage took down banks, brokerages, and payment systems across the continent—a preview of what happens when infrastructure you don't control fails.

The concentration problem isn't just about outages. It's about the fact that a handful of providers now sit underneath the operational resilience of the entire European financial system. When many institutions lean on the same few providers, a single failure—technical, legal, or geopolitical—ripples across all of them at once.

#### Geopolitical and Regulatory Exposure

Model availability can be restricted through US sanctions or export controls. Sensitive data and metadata may be exposed to third-country access. Access to cloud services, updates, or AI models could be restricted in a crisis scenario.

This is the risk that's hardest to price because it's the hardest to imagine. But it's not hypothetical. Export controls have already been used to restrict access to advanced chips and AI models. Sanctions can sever access to services overnight. Data localization mandates can force abrupt architectural changes. For a European company that has built its AI strategy on a US hyperscaler's platform, a geopolitical rupture isn't just a business continuity problem—it's an existential one.

#### The Cost of Sovereignty

According to Eric Bierry, CEO of SBS and Deputy CEO of 74 Software, when CDC, the French public bank, migrated a regulatory reporting service from AWS to France's sovereign SecNumCloud infrastructure, **the cost more than tripled**—even though the underlying product and service stayed exactly the same ([SBS Software, 2026](https://sbs-software.com/insights/artificial-intelligence-data/podcast-ai-in-banking-why-100-sovereign-is-a-myth/)).

True 100% sovereignty isn't achievable anyway. Even domestic infrastructure relies on non-European chips and software somewhere in the stack ([SBS Software, 2026](https://sbs-software.com/insights/artificial-intelligence-data/podcast-ai-in-banking-why-100-sovereign-is-a-myth/)). The question isn't whether you can achieve perfect sovereignty—you can't—but whether you're making deliberate trade-offs between cost, control, and risk.

#### The Compliance Burden

The US CLOUD Act and FISA enable government access to data physically held in the EU where a US nexus exists. This creates a direct conflict with GDPR and the EU's data protection framework. Companies are caught between two legal regimes that make incompatible demands: US law says hand it over; EU law says you can't.

That conflict doesn't resolve itself through better contracts or more careful data mapping. It's structural. And it's the reason "sovereign cloud" keeps coming up in board conversations that would rather be about something else.

---

### What Companies Can Do: Recommendations

The risks are real, but they're not unmanageable. What follows is a set of practical recommendations drawn from regulators, industry bodies, and real-world migrations—not a solution set, but a starting point for institutions that need to act while the strategic questions are still being worked out.

**1. Map concentration risk by service, not just provider.** According to AFME's 2021 paper on cloud computing, banks need to proactively architect for greater resilience by mapping dependencies between services and geographies—identifying, for example, where two different services share a single point of failure, or how an outage in one region may affect the underlying cloud service provider's control plane ([AFME, 2021](https://www.afme.eu/Portals/0/DispatchFeaturedImages/AFME_CloudComputing2021_06-2.pdf)). Concentration risk is an aggregate of your underlying threat scenarios. You need to evaluate each service dependency individually, not just count how many hyperscalers you use.

**2. Adopt a hybrid and multi-cloud strategy.** AFME's recommendations emphasize that banks should maintain an inventory of cloud arrangements and take a risk-based approach using a range of approaches, including multi-cloud and portability ([AFME, 2021](https://www.afme.eu/Portals/0/DispatchFeaturedImages/AFME_CloudComputing2021_06-2.pdf)). In practice: sensitive and regulated data stays within EU-based sovereign clouds, critical systems remain on-premises for maximum control, and less sensitive workloads continue on US hyperscale platforms.

**3. Build a placement and classification logic.** DORA requires financial entities to maintain an ICT third-party risk strategy and policy for ICT services supporting critical or important functions ([DORA](https://www.eba.europa.eu/publications-and-media/press-releases/european-supervisory-authorities-designate-critical-ict-third-party-providers-under-digital)). Classify applications, data, and processes by criticality, regulatory sensitivity, data confidentiality, substitutability, and dependency risk. This determines where each workload should be deployed. EU-based operations may be appropriate for critical services, but they do not guarantee sovereignty on their own—you must also assess control rights, support models, access paths, encryption concepts, and contractual exit options.

**4. Establish and test exit strategies before go-live.** DORA Article 28(8) requires supervised entities to develop transition plans enabling them to remove contracted ICT services and data from third-party providers and securely transfer them to alternatives or in-house ([DORA](https://www.eba.europa.eu/publications-and-media/press-releases/european-supervisory-authorities-designate-critical-ict-third-party-providers-under-digital)). According to the ECB's supervisory guide, exit plans must be realistic, viable, based on plausible scenarios, and include a planned execution timeline compatible with contractual exit clauses ([ECB, 2025](https://www.bankingsupervision.europa.eu/ecb/pub/pdf/ssm.supervisory_guides202507.pt.pdf)). Their feasibility should be tested with independent verification.

**5. Maintain independent control over encryption keys.** According to the European Banking Authority's outsourcing guidelines (EBA/GL/2019/02), financial institutions must retain effective control over encryption keys protecting sensitive data processed or stored by third-party service providers ([EBA, 2019](https://www.kiteworks.com/regulatory-compliance/eba-encryption-key-control-guidelines/)). Without direct key control, institutions cannot demonstrate data sovereignty, execute exit strategies, or guarantee recovery during vendor failures or disputes ([EBA, 2019](https://www.kiteworks.com/regulatory-compliance/eba-encryption-key-control-guidelines/)). The EBA treats encryption key control as a fundamental prerequisite for maintaining operational resilience and data sovereignty when delegating functions to external service providers.

**6. Negotiate collectively.** The AFM and DNB have explicitly warned that widespread reliance on the same providers and infrastructures has led to concentration and systemic risks, and they urge institutions to prepare for disruptive scenarios by collaborating with IT vendors, authorities, and peers ([AFM & DNB, 2025](https://www.afm.nl/en/sector/actueel/2025/okt/pb-digitale-autonomie)). A single company negotiating alone with Amazon or Microsoft has "hardly anything to say"—a few hundred together do.

**7. Invest in European sovereign providers where it makes strategic sense.** The ECB itself chose OVHcloud to provide sovereign cloud services for the digital euro project, with infrastructure operated entirely within the European Union ([OVHcloud, 2026](https://corporate.ovhcloud.com/en-ca/newsroom/news/ovhcloud-digital-euro-ecb/)). De Nederlandsche Bank (DNB) signed a contract with Stackit, the cloud platform owned by Germany's Schwarz Group, to reduce its dependence on American cloud companies ([Techzine, 2026](https://www.techzine.eu/news/infrastructure/140634/dutch-central-bank-chooses-lidl-for-european-cloud/)). Smaller institutions have fewer resources but also lower barriers to adopting European providers—and regulators reward early movers, so an apparent weakness can become a strategic strength.

**8. Treat digital sovereignty as a board-level concentration risk topic.** The AFM and DNB emphasize that reducing digital dependence is a long-term challenge requiring coordinated European solutions, and they call for the development of robust European alternatives to non-EU IT providers ([AFM & DNB, 2025](https://www.afm.nl/en/sector/actueel/2025/okt/pb-digitale-autonomie)). It connects operational resilience, outsourcing governance, technology strategy, data protection, AI adoption, and geopolitical risk management. The question is no longer whether companies should use global technology platforms, but whether they can use them without losing transparency, decision rights, portability, and credible exit options for their most critical services.

---

### The Question That Doesn't Go Away

None of these recommendations solve the underlying problem. They manage it. They buy time. They reduce exposure at the margins. But they don't change the fundamental reality: European companies depend on infrastructure owned by companies that answer to another government's laws.

That dependency isn't going away. Public cloud is too central to AI competitiveness, too embedded in resilience planning, too cost-effective to abandon. The question isn't whether to use it—it's whether the terms of that use can be renegotiated in a way that gives European companies meaningful control over their own security, their own data, and their own competitive future.

The next chapter looks at what solutions actually exist—not just risk management, but structural alternatives. What would a genuinely sovereign cloud stack look like? What's being built, what's working, and what's still missing? And what would it take for European companies to have real options, not just better contracts?

That's where we go next.

* * *

#### References

*   PIFS International, ["Cloud Adoption in the Financial Sector and Concentration Risk"](https://www.pifsinternational.org/cloud-adoption-in-the-financial-sector-and-concentration-risk/)
    
*   Office of the Superintendent of Financial Institutions (OSFI), ["Third-Party Risk Management Guideline"](https://www.osfi-bsif.gc.ca/en/guidance/guidance-library/third-party-risk-management-guideline)
    
*   Bristows, ["AWS US-EAST-1 incident: regulators concentrate on concentration risk"](https://inquisitiveminds.bristows.com/post/102lqkb/aws-us-east-1-incident-regulators-concentrate-on-concentration-risk)
    
*   calQrisk, ["Outsourcing and Third-Party Risk Management for Financial Firms"](https://www.calqrisk.com/resources/insights/outsourcing-and-third-party-risk-management-for-financial-firms)
    
*   FINRA, ["Third-Party Risk Landscape," 2025 Annual Regulatory Oversight Report](https://www.finra.org/rules-guidance/guidance/reports/2025-finra-annual-regulatory-oversight-report/third-party-risk)
    
*   Data Center Dynamics, ["Climate threats to data centers set to surge"](https://www.datacenterdynamics.com/en/news/climate-threats-to-data-centers-set-to-surge-report/)
    
*   XDI, ["Global data centres face rising climate risks"](https://xdi.systems/news/global-data-centres-face-rising-climate-risks-xdi-report-warns-landmark-analysis-of-nearly-9000-sites-reveals-escalating-threat-to-digital-infrastructure/)
    
*   European Supervisory Authorities, DORA CTPP Designation List (November 2025) — [https://www.eba.europa.eu/publications-and-media/press-releases/european-supervisory-authorities-designate-critical-ict-third-party-providers-under-digital](https://www.eba.europa.eu/publications-and-media/press-releases/european-supervisory-authorities-designate-critical-ict-third-party-providers-under-digital)
    
*   ECB, Supervisory Guide on Cloud Outsourcing (July 2025) — [https://www.bankingsupervision.europa.eu/ecb/pub/pdf/ssm.supervisory_guides202507.pt.pdf](https://www.bankingsupervision.europa.eu/ecb/pub/pdf/ssm.supervisory_guides202507.pt.pdf)
    
*   EBA, Outsourcing Guidelines (EBA/GL/2019/02) — [https://www.kiteworks.com/regulatory-compliance/eba-encryption-key-control-guidelines/](https://www.kiteworks.com/regulatory-compliance/eba-encryption-key-control-guidelines/)
    
*   AFM & DNB, "AFM and DNB warn of systemic risks in the financial sector from digital dependence" (October 2025) — [https://www.afm.nl/en/sector/actueel/2025/okt/pb-digitale-autonomie](https://www.afm.nl/en/sector/actueel/2025/okt/pb-digitale-autonomie)
    
*   OVHcloud, "OVHcloud to provide sovereign cloud services for the ECB digital euro" (March 2026) — [https://corporate.ovhcloud.com/en-ca/newsroom/news/ovhcloud-digital-euro-ecb/](https://corporate.ovhcloud.com/en-ca/newsroom/news/ovhcloud-digital-euro-ecb/)
    
*   Techzine, "Dutch central bank chooses Lidl for European Cloud" (April 2026) — [https://www.techzine.eu/news/infrastructure/140634/dutch-central-bank-chooses-lidl-for-european-cloud/](https://www.techzine.eu/news/infrastructure/140634/dutch-central-bank-chooses-lidl-for-european-cloud/)
    
*   SBS Software, "AI in banking | Part 3: Why '100% sovereign' is a myth" (September 2026) — [https://sbs-software.com/insights/artificial-intelligence-data/podcast-ai-in-banking-why-100-sovereign-is-a-myth/](https://sbs-software.com/insights/artificial-intelligence-data/podcast-ai-in-banking-why-100-sovereign-is-a-myth/)
    
*   AFME, "Cloud Computing in Capital Markets" (June 2021) — [https://www.afme.eu/Portals/0/DispatchFeaturedImages/AFME_CloudComputing2021_06-2.pdf](https://www.afme.eu/Portals/0/DispatchFeaturedImages/AFME_CloudComputing2021_06-2.pdf)
    
*   FISA (Foreign Intelligence Surveillance Act), including Section 702 provisions — [https://www.law.cornell.edu/wex/foreign_intelligence_surveillance_act](https://www.law.cornell.edu/wex/foreign_intelligence_surveillance_act)
    
*   US CLOUD Act — [https://www.congress.gov/bill/115th-congress/senate-bill/2383](https://www.congress.gov/bill/115th-congress/senate-bill/2383)

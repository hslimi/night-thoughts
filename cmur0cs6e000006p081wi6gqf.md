---
title: "The Old Trade-Off: Vendor vs. In-House, Before AI Changed the Rules"
datePublished: 2026-10-02T13:37:43.359Z
cuid: cmur0cs6e000006p081wi6gqf
slug: the-old-trade-off-vendor-vs-in-house-before-ai-changed-the-rules
cover: https://cdn.hashnode.com/uploads/covers/6a92730f9a9aa7f72e74fdf4/2a6f1576-3f47-4503-a1fe-f38d0b0503ee.jpg
tags: ai, vendor, finance, public-cloud

---

*This is the first chapter of **Built to Leave**, a series on cloud dependency, sovereignty, and the architecture that makes exit possible. The series follows the problem from its origins — the build-vs-buy trade-off that predates AI — through the structural costs of cloud dependency, the work required to regain control, and the architectural shift that AI workloads are now forcing. Full table of contents: [nightthoughts.hashnode.dev/build-to-leave](https://nightthoughts.hashnode.dev/build-to-leave)*

---

Long before anyone in finance was talking about AI, institutions were already wrestling with one of the oldest questions in enterprise technology: build it yourself, or buy it from someone else. It's a decision every bank, insurer, and financial services firm has made repeatedly, across decades, for every new capability that came along — core banking systems, trading platforms, risk engines, data infrastructure. The technology changed. The underlying dilemma didn't.

This article isn't about AI yet. It's about understanding the trade-off as it existed before AI entered the picture — because you can't understand how AI is reshaping the game until you understand the board it's being played on.

## A brief chronology

Financial institutions have swung between these two poles for a long time, and rarely by pure technical logic — often by cost pressure, regulation, or the scars of a previous decision gone wrong.

In earlier decades, many institutions built almost everything in-house, out of necessity more than preference — the vendor ecosystem for specialized financial technology simply didn't exist yet. Core systems were custom, maintained by large internal IT departments, because there was no market offering an alternative.

As the vendor landscape matured, the pendulum swung toward buying. Specialized providers emerged for almost every function — trading systems, compliance tooling, payment processing, data feeds — and outsourcing that work became the default, because building it yourself no longer made economic sense against a mature, specialized alternative.

More recently, the pendulum has been swinging back, at least partially. Institutions that outsourced heavily started reckoning with the risks of that dependency, and many began reinvesting in in-house engineering capability — not to replace vendors entirely, but to regain control over what they saw as strategically important.

Neither swing was permanent, and neither was universally correct. What's stayed constant is the underlying trade-off itself.

## The case for the vendor

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
    

## The case for in-house

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
    

## The speed trap: how both paths lead to the same mess

There's a dimension to this trade-off that doesn't show up in cost comparisons or risk matrices, but that anyone who has actually shipped software in a bank will recognize immediately: speed pressure distorts both paths, and it tends to distort them toward the same outcome.

When the business sees an opportunity, the instinct is to move before competitors do. On the in-house side, that pressure produces what I'd call **commando mode** — or sniper mode: build exactly what's needed, nothing more, and move fast. No time for the full picture. No time to future-proof. Just enough to seize the opportunity, now, while it's there. And for day one, this works. It's often the *right* call — a mature, fully governed build process would have missed the window entirely.

The problem is what happens next. As soon as that commando-mode build reaches production and the business succeeds, the very success creates pressure the system was never built to absorb. It doesn't scale. Clients want more than the minimal version can deliver. The business struggles to understand why something that clearly works can't simply be extended — surely if it does *this*, it can do *that* too? And underneath, the parts that were skipped in the rush — proper security, authentication, resilience — are exactly the parts that are hardest and most expensive to retrofit once real usage and real data are flowing through the system.

The vendor path isn't immune to its own version of this trap, just from a different direction. Getting real value out of a vendor platform — configuring it properly, building the features specific to your business — requires expertise, and that expertise is often scarce and expensive. Institutions frequently end up dependent on a small number of specialists who understand the vendor's tool deeply, and just as often end up building a growing constellation of **satellite applications** around the vendor platform to bridge the gaps it doesn't cover natively. Ironically, by the time all of that is stitched together, time to market on the vendor path can end up *slower* than a commando-mode in-house build — the very speed advantage vendors are supposed to offer gets eaten by integration and customization overhead.

Here's the uncomfortable convergence: **whichever path you take, the default outcome, without deliberate intervention, is the same** — a sprawling landscape of small applications in production, built under time pressure, neither scalable nor properly secured, each one requiring real ongoing effort, spread across teams worldwide, just to keep it up and running.

This is where I think the real discipline lives — not in choosing build or buy correctly in the abstract, but in resisting the urge to let either path run on pure speed indefinitely. At some point, an institution has to deliberately slow down: organize what's been built, structure it properly, size the actual opportunity rather than the emergency that created it, and identify which of these applications are mature and important enough to deserve real investment — and which should be retired, consolidated, or never should have reached production in their current form in the first place.

## Neither side is "safe"

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

### References

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
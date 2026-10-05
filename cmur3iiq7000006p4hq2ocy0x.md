---
title: "The Sovereignty Illusion: What Companies Get Wrong About Cloud Independence"
datePublished: 2026-10-02T15:06:09.876Z
cuid: cmur3iiq7000006p4hq2ocy0x
slug: the-sovereignty-illusion-what-companies-get-wrong-about-cloud-independence
cover: https://cdn.hashnode.com/uploads/covers/6a92730f9a9aa7f72e74fdf4/9db712eb-14bc-4f6d-bfd3-6830e6342c6b.jpg
tags: data, cloud-computing, finance, sovereignty

---

*This is the third chapter of **Built to Leave**, a series on cloud dependency, sovereignty, and the architecture that makes exit possible. The series follows the problem from its origins — the build-vs-buy trade-off that predates AI — through the structural costs of cloud dependency, the work required to regain control, and the architectural shift that AI workloads are now forcing. Full table of contents: [nightthoughts.hashnode.dev/build-to-leave](https://nightthoughts.hashnode.dev/build-to-leave)*

---

In the first chapter of this series, I looked at the oldest trade-off in enterprise technology: build it yourself, or buy it from someone else. In the second, I looked at how two forces—defensive security and offensive competitiveness—are pushing financial institutions toward the same infrastructure at the same time. This chapter looks at the foundation both of those forces run on, and the uncomfortable question underneath it: **whose cloud is it, really?**

There's a phrase that captures the core misunderstanding I want to unpack here: *"Your data, their laws."* It sounds provocative, maybe even alarmist. But for a European company storing data with a US-headquartered cloud provider, it is a literal description of the legal reality. The US CLOUD Act and FISA allow US authorities to compel US-incorporated companies to hand over data—regardless of where that data is physically stored. A server in Frankfurt does not put that data beyond the reach of US law if the company operating it is subject to US jurisdiction.

That's the sovereignty illusion. For years, "sovereign cloud" has been sold to European companies as a matter of data residency: keep the bits inside EU borders, and you've solved the problem. But jurisdiction follows the company, not the server. And as long as the parent company answers to another government's laws, "complete sovereignty" remains out of reach.

This matters most for Europe, where the gap between ambition and reality is widest. US hyperscalers control over 70% of the European cloud market. European providers hold around 15%, a share that has barely moved despite years of investment and political will. DORA has given European supervisors new powers over critical third-party providers, but oversight is not the same as alternatives. And the concentration risk isn't theoretical—the October 2025 AWS US-East-1 outage took down European banks, brokerages, and payment systems, a preview of what's at stake when the infrastructure you don't control fails.

For US or Chinese companies, this is rarely a live question—they operate under the same jurisdiction as their dominant cloud providers. For European companies, it is unavoidable. So what does "independence" actually mean when both your security posture and your competitive AI capability depend on infrastructure owned by someone else, operating under someone else's laws? That's the question this chapter sits with. It doesn't have a tidy answer—but the first step is naming the problem clearly: **your data, their laws.** Everything else follows from there.

---

## Why Public Cloud Is Non-Negotiable

Before getting into the risks, it's worth being honest about why European companies can't simply walk away from public cloud. The dependency isn't a failure of strategy; it's a rational response to three converging pressures.

**AI requires scale.** Generative AI has deepened dependency across three layers: specialized chips (Nvidia-dominated), foundation models (GPT, Gemini, Claude), and integrated AI platforms from hyperscalers. Building that stack in-house is not a realistic option for most companies. The compute requirements alone—training runs costing tens of millions, inference at scale requiring global distribution—put it out of reach for any institution whose core business is finance, not infrastructure.

**Resilience demands it.** Rising climate and geopolitical risks are pushing infrastructure resilience requirements toward multi-region, geographically diversified setups almost as a baseline expectation now, not a best practice for the ambitious. One global analysis of nearly 9,000 data centers found that a meaningful share already sit in locations facing high or moderate physical climate risk. A separate analysis put the share of capacity exposed to acute climate hazards—flooding, extreme wind, wildfire—at close to four in five facilities worldwide. Meeting that bar in-house means duplicating infrastructure across regions, at a cost and complexity that grows with every added region.

**Cost efficiency is real.** For years, US hyperscalers offered European companies unmatched scalability and cost efficiency. The pay-as-you-go model converts large fixed investments into variable costs. For institutions under margin pressure, that flexibility is not a luxury—it's a competitive necessity.

**Regulatory pressure cuts both ways.** DORA requires robust operational resilience, but it also acknowledges that cloud concentration is a systemic risk. The regulation gives supervisors new powers over critical third-party providers, but oversight is not the same as alternatives. A covered entity using a designated provider gets some assurance that the provider is being supervised, but the covered entity remains accountable for its own risk management.

The point is this: public cloud isn't a choice European companies can undo. The question is what that dependency actually costs—and whether the price is being measured honestly.

---

## The Risks: What Companies Are Actually Paying For

### The Jurisdiction Trap

The US CLOUD Act and FISA allow US authorities to compel US-incorporated companies to hand over data regardless of where it's stored. This creates a direct conflict with GDPR and the EU's data protection framework. A server in Frankfurt is legally an American server. Data residency only answers where data sits, not who can be compelled to hand it over.

This isn't a theoretical concern. The CLOUD Act was designed precisely to resolve conflicts between US law enforcement demands and foreign data protection laws—and it resolves them in favor of US access. For a European company, that means the legal protections you've built around data residency can be overridden by a legal order you have no standing to contest.

### Concentration Risk

According to the Dutch Authority for the Financial Markets (AFM) and De Nederlandsche Bank (DNB), the Dutch financial sector faces increasing systemic risks stemming from its growing reliance on a limited number of non-European IT service providers. The regulators caution that this dependency amplifies the risk of concentration and systemic disruption, where a failure at a single provider could impact large segments of the financial sector ([AFM & DNB, 2025](https://www.afm.nl/en/sector/actueel/2025/okt/pb-digitale-autonomie)).

More than 30% of significant EU institutions' total outsourcing budgets flow to just 10 providers. In 2025, 29% of major ICT incidents reported across the EU financial sector originated from third-party provider failures. The October 2025 AWS US-East-1 outage took down banks, brokerages, and payment systems across the continent—a preview of what happens when infrastructure you don't control fails.

The concentration problem isn't just about outages. It's about the fact that a handful of providers now sit underneath the operational resilience of the entire European financial system. When many institutions lean on the same few providers, a single failure—technical, legal, or geopolitical—ripples across all of them at once.

### Geopolitical and Regulatory Exposure

Model availability can be restricted through US sanctions or export controls. Sensitive data and metadata may be exposed to third-country access. Access to cloud services, updates, or AI models could be restricted in a crisis scenario.

This is the risk that's hardest to price because it's the hardest to imagine. But it's not hypothetical. Export controls have already been used to restrict access to advanced chips and AI models. Sanctions can sever access to services overnight. Data localization mandates can force abrupt architectural changes. For a European company that has built its AI strategy on a US hyperscaler's platform, a geopolitical rupture isn't just a business continuity problem—it's an existential one.

### The Cost of Sovereignty

According to Eric Bierry, CEO of SBS and Deputy CEO of 74 Software, when CDC, the French public bank, migrated a regulatory reporting service from AWS to France's sovereign SecNumCloud infrastructure, **the cost more than tripled**—even though the underlying product and service stayed exactly the same ([SBS Software, 2026](https://sbs-software.com/insights/artificial-intelligence-data/podcast-ai-in-banking-why-100-sovereign-is-a-myth/)).

True 100% sovereignty isn't achievable anyway. Even domestic infrastructure relies on non-European chips and software somewhere in the stack ([SBS Software, 2026](https://sbs-software.com/insights/artificial-intelligence-data/podcast-ai-in-banking-why-100-sovereign-is-a-myth/)). The question isn't whether you can achieve perfect sovereignty—you can't—but whether you're making deliberate trade-offs between cost, control, and risk.

### The Compliance Burden

The US CLOUD Act and FISA enable government access to data physically held in the EU where a US nexus exists. This creates a direct conflict with GDPR and the EU's data protection framework. Companies are caught between two legal regimes that make incompatible demands: US law says hand it over; EU law says you can't.

That conflict doesn't resolve itself through better contracts or more careful data mapping. It's structural. And it's the reason "sovereign cloud" keeps coming up in board conversations that would rather be about something else.

---

## What Companies Can Do: Recommendations

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

## The Question That Doesn't Go Away

None of these recommendations solve the underlying problem. They manage it. They buy time. They reduce exposure at the margins. But they don't change the fundamental reality: European companies depend on infrastructure owned by companies that answer to another government's laws.

That dependency isn't going away. Public cloud is too central to AI competitiveness, too embedded in resilience planning, too cost-effective to abandon. The question isn't whether to use it—it's whether the terms of that use can be renegotiated in a way that gives European companies meaningful control over their own security, their own data, and their own competitive future.

The next chapter looks at what solutions actually exist—not just risk management, but structural alternatives. What would a genuinely sovereign cloud stack look like? What's being built, what's working, and what's still missing? And what would it take for European companies to have real options, not just better contracts?

That's where we go next.

* * *

### References

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
---
title: "Beyond DeepSeek and Qwen: Five Teams Building China’s Open-Source AI Foundations"
datePublished: 2026-10-27T15:22:00.017Z
cuid: cmvqu36k9000002mvg5ct6ktn
slug: beyond-deepseek-and-qwen-five-teams-building-china-s-open-source-ai-foundations
cover: https://cdn.hashnode.com/uploads/covers/6a92730f9a9aa7f72e74fdf4/a8c69d5f-4021-4c01-ae28-d6ce6d9d02b9.png
tags: ai, machine-learning, china, open-source, llm

---

The most important Chinese contribution to open-source AI may not be a model at all.

International coverage tends to organize Chinese AI around a familiar cast: DeepSeek for reasoning, Qwen for open-weight models, and a rotating group of technology giants competing for the next benchmark headline. That focus is understandable. Frontier models are visible, measurable, and easy to compare.

But powerful AI systems are not built from model weights alone. They require document parsers, retrieval models, training frameworks, reinforcement-learning infrastructure, evaluation tools, and carefully filtered datasets. These components rarely produce viral demonstrations. Yet they determine whether researchers and companies can reproduce results, adapt models, and deploy them economically.

This is where a different group of Chinese contributors deserves attention. They are not literally secret: some are government-supported, others belong to major companies, and most actively promote their work. They are “hidden” primarily from an international conversation that treats model launches as the main event and infrastructure as an afterthought.

Here are five worth knowing.

## 1. Shanghai AI Lab: Building the Machinery Around Models

Shanghai AI Laboratory’s most consequential work may be its attempt to cover almost the entire development pipeline.

[MinerU](https://github.com/opendatalab/MinerU) converts complex documents into machine-readable content. [OpenDataLab](https://opendatalab.com/) distributes datasets. [XTuner](https://github.com/InternLM/xtuner) supports training and fine-tuning. [LMDeploy](https://github.com/InternLM/lmdeploy) handles inference and serving. [OpenCompass](https://github.com/open-compass/opencompass) provides evaluation infrastructure. The InternLM and Intern-S model families sit above this supporting stack.

MinerU is the clearest example of international reach. Its repository now has roughly [82,600 GitHub stars](https://github.com/opendatalab/MinerU)—evidence of substantial developer interest, even though stars should not be confused with production adoption.

The laboratory’s scientific work also produced a more unusual achievement. According to the paper’s [declaration of AI use](https://arxiv.org/abs/2608.03738), an internal version of Intern-S2 assisted mathematician Jiesong Zhang through multiple dialogue rounds while developing arguments for a proof of the codimension-one case of the Ghys conjecture, including complex dimension three. The human author independently verified the mathematics, and a Peking University team subsequently formalized the central results in Lean.

That is not autonomous mathematical discovery. It is something more credible and, in some ways, more useful: evidence that a model can participate in a serious human-guided research process.

Shanghai AI Lab should nevertheless be described accurately. It is a [government-supported institutional powerhouse](https://thediplomat.com/2020/08/chinas-artificial-intelligence-government-strategy-and-its-capabilities/), not a scrappy underground collective. Its tools are significant, but claims that global startups universally depend on them require stronger adoption evidence. The achievement is the breadth and usefulness of the portfolio—not a proven monopoly over AI infrastructure.

## 2. BAAI: Making Retrieval Part of the Open-Source Foundation

The Beijing Academy of Artificial Intelligence, or BAAI, illustrates why some of the most useful AI components never become household names.

Its [BGE family](https://github.com/FlagOpen/FlagEmbedding) focuses on embeddings and reranking: the machinery that helps systems retrieve relevant information before a language model generates an answer. This is central to retrieval-augmented generation, enterprise search, and knowledge-based assistants.

[BGE-M3](https://github.com/FlagOpen/FlagEmbedding/tree/master/FlagEmbedding/abc/inference), for example, supports more than 100 languages, inputs of up to 8,192 tokens, and dense, sparse, and multi-vector retrieval within one model family.

That combination addresses practical engineering problems rather than offering a spectacular chatbot demonstration. Developers building multilingual retrieval systems need components that can be downloaded, evaluated, fine-tuned, and integrated into existing pipelines. BGE gives them a reusable starting point.

The broader lesson is that open-source progress does not always arrive as a smarter conversational model. Sometimes it arrives as a better way to connect models to information. Retrieval infrastructure may never dominate social-media discussions, but without it, many impressive demonstrations collapse into unreliable systems with no dependable access to external knowledge.

## 3. OpenBMB: Arguing That Small Models Matter

OpenBMB, a collaboration associated with Tsinghua University’s NLP researchers and ModelBest, has made efficiency its central technical argument.

Its [MiniCPM family](https://github.com/OpenBMB/MiniCPM) targets local and resource-constrained deployment rather than simply maximizing parameter count. This matters because most developers do not operate frontier-scale infrastructure. Models that run on laptops, phones, and modest servers expand the group of people able to experiment, customize, and build.

An [independent Artificial Analysis evaluation](https://artificialanalysis.ai/models/minicpm-v4-6-1-3b) of MiniCPM-V 4.6’s 1.3B variant identified it as a new efficiency frontier on its intelligence-versus-parameter comparison. The same report describes OpenBMB as a Tsinghua–ModelBest collaboration founded in 2022 and notes the model’s Apache 2.0 release.

The project’s more interesting contribution is increasingly the material released around the models. The [MiniCPM5 repository](https://github.com/OpenBMB/MiniCPM) lists training datasets covering web data, code, supervised fine-tuning, agent behavior, and reinforcement learning.

Weights allow experimentation. Data and training resources help explain how the result was produced.

OpenBMB’s efficiency claims still require model-by-model scrutiny, particularly when benchmark tables come from the authors. But its strategic insight is sound: open-source AI becomes more democratic not only when the largest models are released, but also when capable systems fit within realistic computing budgets.

## 4. ByteDance Seed: Opening the Reinforcement-Learning Workshop

ByteDance is hardly an obscure company. Its Seed research organization nevertheless belongs in this discussion because some of its most valuable open-source work concerns the training process rather than consumer products.

The [verl framework](https://github.com/volcengine/verl) provides infrastructure for reinforcement-learning post-training. It supports algorithms such as PPO and GRPO and integrates with systems including FSDP, Megatron-LM, vLLM, and SGLang.

That matters because modern reasoning models depend heavily on post-training, yet the necessary infrastructure is difficult to reproduce. Researchers must coordinate training, generation, reward calculation, distributed computation, and rapidly changing model states. A model card alone reveals little about how to make that process work.

[DAPO](https://arxiv.org/abs/2503.14476), developed by ByteDance Seed with Tsinghua AIR and collaborators, pushed further by releasing the algorithm, code infrastructure, and dataset for a large-scale reinforcement-learning system. The project also published [reproduction scripts and training records](https://github.com/BytedTsinghua-SIA/DAPO).

This is a particularly meaningful form of openness. It moves beyond “here are the finished weights” toward “here is a substantial part of the workshop used to produce them.”

The broader community benefits even when it does not adopt DAPO itself. Published techniques and working code provide baselines that other researchers can inspect, modify, criticize, and improve.

## 5. OpenCSG: Treating Data as Infrastructure

OpenCSG represents the least glamorous layer of all: datasets and the systems used to manage them.

Its Chinese corpus projects—including [Fineweb-Edu-Chinese, Cosmopedia-Chinese, and Smoltalk-Chinese](https://opencsg.com/blog/72)—focus on filtering, scoring, formatting, and preparing text for training. OpenCSG says these datasets contributed to the Chinese training material used for MiniCPM4, offering a concrete example of one open project feeding another.

Its [CSGHub platform](https://github.com/OpenCSGs/CSGHub) addresses a different problem: governing models, datasets, code, and related assets throughout their lifecycle.

This work deserves attention because dataset quality often determines whether a training run succeeds. Scale without provenance, deduplication, licensing clarity, and quality control can produce little more than expensive noise.

But OpenCSG also demonstrates why “open” should never be accepted as a blanket description. The license for [Fineweb-Edu-Chinese V2.2](https://opencsg.com/datasets/AI-ModelScope/fineweb-edu-chinese-v2.2) asks commercial users to contact the organization and obtain permission. That does not erase the dataset’s value, but it is materially different from unrestricted Apache-licensed reuse.

Recognizing community contributions should not mean abandoning license scrutiny. It should mean examining each artifact individually.

## The Real Story Is an Ecosystem, Not a Secret Conspiracy

These organizations do not share one governance model or one motive. Shanghai AI Lab and BAAI are institutional research organizations. OpenBMB connects academic and commercial participants. ByteDance Seed belongs to a technology giant. OpenCSG combines community resources with commercial platform ambitions.

Their openness is therefore neither pure altruism nor meaningless marketing. Open releases can attract developers, establish technical standards, recruit researchers, improve domestic infrastructure, and create commercial opportunities—all while providing genuine public value.

The appropriate response is neither uncritical celebration nor automatic suspicion. It is evaluation based on concrete questions:

- Are the artifacts reusable outside the original organization?
- Are the code, data, and training details sufficient for reproduction?
- Are the licenses actually permissive?
- Is maintenance sustained after the announcement?
- Are external developers building on the work?
- Are performance claims independently reproduced?

By those standards, the five organizations above have made contributions worth serious attention, even if none individually justifies a grand narrative about secretly powering global AI.

The international community should stop treating Chinese open source as a story about a few famous model brands. The deeper story is an expanding network of laboratories, companies, academic teams, and data projects supplying different parts of the AI development process.

Some of their most important releases will never trend like a frontier chatbot. But a parser that makes documents usable, an embedding model that improves retrieval, a training framework that exposes reinforcement-learning recipes, or a dataset that makes experimentation cheaper can influence far more work than its public recognition suggests.

These players are not hidden because their work is unavailable. They are hidden because we have been looking too narrowly at what counts as an AI achievement.

## References

1. [MinerU — OpenDataLab’s document-parsing project](https://github.com/opendatalab/MinerU)
2. [OpenDataLab — Dataset platform](https://opendatalab.com/)
3. [XTuner — Training and fine-tuning framework](https://github.com/InternLM/xtuner)
4. [LMDeploy — Model compression, deployment, and serving toolkit](https://github.com/InternLM/lmdeploy)
5. [OpenCompass — Model-evaluation platform](https://github.com/open-compass/opencompass)
6. [Jiesong Zhang, “Codimension-One Holomorphic Anosov Diffeomorphisms”](https://arxiv.org/abs/2608.03738)
7. [The Diplomat — Background on Shanghai AI Laboratory’s government support](https://thediplomat.com/2020/08/chinas-artificial-intelligence-government-strategy-and-its-capabilities/)
8. [FlagEmbedding — Home of the BGE embedding and reranking models](https://github.com/FlagOpen/FlagEmbedding)
9. [BGE-M3 — Multilingual, multi-functionality, and multi-granularity retrieval](https://github.com/FlagOpen/FlagEmbedding/tree/master/FlagEmbedding/abc/inference)
10. [MiniCPM — OpenBMB’s efficient multimodal model family](https://github.com/OpenBMB/MiniCPM)
11. [Artificial Analysis — Independent assessment of MiniCPM-V 4.6 1.3B](https://artificialanalysis.ai/models/minicpm-v4-6-1-3b)
12. [verl — Reinforcement-learning training infrastructure for language models](https://github.com/volcengine/verl)
13. [DAPO — An Open-Source LLM Reinforcement Learning System at Scale](https://arxiv.org/abs/2503.14476)
14. [DAPO — Code, reproduction scripts, and training records](https://github.com/BytedTsinghua-SIA/DAPO)
15. [OpenCSG — Chinese-language training datasets and MiniCPM4](https://opencsg.com/blog/72)
16. [CSGHub — Open-source platform for managing AI assets](https://github.com/OpenCSGs/CSGHub)
17. [Fineweb-Edu-Chinese V2.2 — Dataset card and licensing conditions](https://opencsg.com/datasets/AI-ModelScope/fineweb-edu-chinese-v2.2)

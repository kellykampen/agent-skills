---
name: model-classifier
description: >-
  Classify any task description into the single best underlying AI model to run it on, scored
  on cost, intelligence, and taste — across a roster of current frontier and budget models
  (Claude Opus, Sonnet, Haiku, and Fable; GPT/Codex including GPT-5.6 Sol/Terra/Luna; Grok; Gemini Pro and Flash; Kimi; GLM).
  Returns a MODEL, not a harness or CLI — which wrapper/tool actually runs that model is the
  caller's decision. Use this BEFORE delegating work to a subagent, launching an Agent/Workflow
  call, or deciding which model should implement, review, or design a piece of work — even if
  the request is phrased as "who should build this," "what model should I use for this," or
  "is this a Sonnet or Opus task." Consult this skill rather than picking a model from memory
  or habit — its ratings and thresholds are meant to be a single, consistent source of truth
  and get corrected as real results come in.
metadata:
  author: kellykampen
  version: "1.0.3"
---

# Model Classifier

One task description goes in, one model recommendation + a one-line reason comes out. This
exists so model-selection decisions (which model builds/reviews/designs a given piece of work)
are made the same way every time, instead of re-litigated per task or per mood.

**This skill names models, not harnesses.** "Model" is the underlying AI (GPT-5.5 Codex, Claude
Opus 4.8, Kimi K2.7 Code, ...); "harness" is whatever CLI/wrapper/API call actually invokes it
(Claude Code, Codex CLI, `agy`, a shell wrapper, a raw API call). Which harness to use is the
caller's decision, made separately — often the same model is reachable through more than one
harness, and that mapping changes over time. Answer with the model only.

## The lineup

### Reading the scale

Every rating is **1–9, and higher is always better on that axis** — including cost:

| Score | Cost (cost-effectiveness) | Intelligence | Taste |
|---|---|---|---|
| **9** | Nearly free to run — use it liberally | Frontier reasoning; trust it unsupervised on the hardest problems | Exceptional design/copy/API judgment; output reads as expert-crafted |
| **7–8** | Cheap; fine as a resident workhorse | Handles complex, multi-step work reliably | Good judgment; safe for most user-facing work (7 is the user-facing floor) |
| **5–6** | Noticeably priced; fine for targeted use | Solid on well-specified work; struggles with ambiguity | Serviceable but generic; don't let it set visual/API patterns |
| **3–4** | Expensive; burns real budget/quota | Routine tasks only | Below the bar for anything users see |
| **1–2** | Very expensive — reserve for what nothing else can do | Only trivial, known-answer work | No design judgment; mechanical output only |

So a **cost of 9 means very cheap**, not very costly — think of every number as "how much do
you want this," never "how much does it hurt." Cost ranks real per-token price across
providers (Kimi/GLM cheapest, Gemini slightly dearer, GPT dearer still, Fable dearest),
tempered by which quota it draws from.

### The table

| Model | Cost | Intelligence | Taste |
|---|---|---|---|
| **GLM-5.2** ⚠️ | 9 | 7 | 5 |
| **Kimi K2.7 Code** ⚠️ | 9 | 7 | 5 |
| **Claude Haiku 4.5** | 9 | 2 | 2 |
| **Gemini 3.5 Flash** ⚠️ | 8 | 6 | 4 |
| **Gemini 3.1 Pro** ⚠️ | 8 | 8 | 6 |
| **Grok 4.5** ⚠️ | 8 | 9 | 8 |
| **GPT-5.5 (Codex)** | 6 | 8 | 5 |
| **GPT-5.6 Luna** ⚠️ | 6 | 9 | 8 |
| **GPT-5.6 Sol** ⚠️ | 6 | 9 | 8 |
| **GPT-5.6 Terra** ⚠️ | 6 | 9 | 9 |
| **Claude Sonnet 5** | 5 | 5 | 7 |
| **Claude Opus 4.8** | 4 | 8 | 8 |
| **Claude Fable 5** | 2 | 9 | 9 |

⚠️ = estimated, not yet field-validated. The Claude rows and GPT-5.5 (Codex) numbers are
hand-tuned from lived experience (cost spread to follow real price ordering). GLM-5.2, Kimi
K2.7 Code, and both Gemini rows are best-guess placements from public benchmarks and pricing,
not lived experience — treat them as a starting point and correct them (or ask to correct them)
the first time a real task proves one wrong in either direction.

Model-name notes, so recommendations stay unambiguous:
- **GPT-5.5 (Codex)** = OpenAI's 5.5-generation coding model (the thing the Codex CLI runs).
  Say "GPT-5.5 (Codex)"; the caller picks how to reach it.
- **Grok 4.5** = xAI's fast, very capable frontier model. In Pi it is reachable via `xai-auth/grok-4.5` or OpenRouter `x-ai/grok-4.5`; prefer the direct xAI route when available. Treat it as a cheap Fable-adjacent model until field data says otherwise.
- **GPT-5.6 Luna / Sol / Terra** = OpenAI 5.6 family models available in Pi via `openai-codex` and OpenRouter. Treat them as Fable-tier reasoning/design options on OpenAI/Codex/OpenRouter quota. Default interpretation: Luna = broad high-taste generalist, Sol = hard reasoning/coding, Terra = strongest taste/product/design.
- **Kimi K2.7 Code** is Moonshot's coding flagship; a "highspeed" serving tier of the same
  model exists — that's a harness/serving choice, not a different recommendation.
- **GLM-5.2** is Z.ai's flagship (1M context — the only non-Claude, non-GPT row with one).

## Why these three axes, and how they interact

- **Intelligence** — how hard a problem you can hand this model *unsupervised* and trust the
  result. This is the main lever for anything genuinely difficult: novel architecture,
  ambiguous requirements, security/money-logic reasoning, debugging something nobody's seen
  before.
- **Taste** — UI/UX judgment, code quality, API design sense, copywriting. A model can be
  highly intelligent and still make ugly, over-engineered, or tone-deaf choices — taste is a
  separate skill from raw reasoning power, and it's the axis that decides whether end users or
  teammates will notice the output was AI-assisted.
- **Cost** — a tie-breaker, not a veto. When two models would both do the job well, prefer the
  cheaper one. When they disagree — i.e. the cheap model is measurably less capable — **the
  priority order is intelligence > taste > cost.** Never let cost talk you into a model that
  can't actually do the job; escalating to a pricier model costs less than shipping mediocre or
  broken work and redoing it.

These are defaults, not hard limits. If a cheaper model's output doesn't clear the bar, rerun
or redo the work on a smarter model without asking — judge the output you got, not the price
tag you expected to pay.

## Decision procedure

Read the task description and place it into whichever of these fits best. They're ordered
roughly cheapest-first because that's the instinct to check first, not because you should
default there — go through them in order and stop at the first real match.

1. **Trivial / mechanical / known-answer** — renames, boilerplate, running a frozen regression
   checklist, simple greps, anything where the "right answer" is already fully determined and
   there's nothing to judge. → **Claude Haiku 4.5** (cost 9, and intelligence 2 is plenty when
   there's nothing to reason about). If Haiku isn't available in this context, **GLM-5.2** or
   **Gemini 3.5 Flash** are the cheap fallbacks.

2. **Bulk / mechanical with a clear spec** — implementation where the ticket already fully
   specifies behavior, data-processing/migration scripts, repetitive multi-file changes that
   follow one pattern. Needs real intelligence to execute correctly but no taste calls. →
   **Kimi K2.7 Code** or **GLM-5.2** (cost 9, intelligence 7 comfortably covers specced work —
   pick either; alternating between them is free provider diversity). For the trickiest items
   in a batch, or when the work is subtle enough that intelligence 7 feels marginal, step up to
   **GPT-5.5 (Codex)**, **Grok 4.5**, **GPT-5.6 Sol**, or **Gemini 3.1 Pro**: prefer GPT-5.5 (Codex) for standard hands-on coding, Grok 4.5 when you need a fast/cheap frontier pass, GPT-5.6 Sol when intelligence 8 feels marginal, and Gemini 3.1 Pro for analysis, long-context reading, or when the OpenAI/xAI sides are saturated.

3. **User-facing — UI, copy, API/product design** — anything an end user or another engineer
   will read, look at, or call. This is a **hard filter, not just a preference**: taste must be
   **≥ 7**, because a low-taste model will produce something that visibly reads as
   under-designed no matter how "correct" it is. Under the table above that filter currently
   clears **Claude Sonnet 5 (7), Claude Opus 4.8 (8), Claude Fable 5 (9), Grok 4.5 (8), and GPT-5.6 Luna/Sol/Terra (8/8/9)**. Within that shortlist, apply intelligence > taste > cost: simple polish or small UI tasks → Sonnet 5; standard-to-complex design/API work → Grok 4.5, GPT-5.6 Luna/Terra, or Opus 4.8; genuinely novel or high-stakes design (new product surface, pricing page, something that sets a pattern others will copy) → Claude Fable 5 or GPT-5.6 Terra.

4. **Review of a plan or implementation** — judging someone else's design doc or PR, not
   producing new work. → **Claude Opus 4.8** as the default reviewer (intelligence 8 is what a
   good review needs, at a fraction of Fable's cost). Escalate to **Claude Fable 5** only when
   the thing under review is *itself* high-stakes by the same bar as #5 — security models,
   money-logic, architecture, something expensive and hard to detect if wrong (e.g. reviewing a
   payment-webhook signature check, not a routine UI PR). Optionally add **GPT-5.5 (Codex)** or
   **Gemini 3.1 Pro** as a second, genuinely independent pass on either tier — not as a
   cost-saving substitute, but because a different model family catches different mistakes than
   whichever family wrote the thing being reviewed.

5. **Hardest reasoning / high-stakes judgment** — new architecture, security models,
   money-logic design, postmortems, or anything where being wrong is expensive and hard to
   detect after the fact. → **Claude Fable 5**, **GPT-5.6 Terra/Sol**, or **Grok 4.5**. Fable remains the conservative gold standard; GPT-5.6 Terra/Sol are Fable-tier OpenAI options; Grok 4.5 is the cheap/fast frontier option. Use these as escalations, not residents: get the specific answer, don't leave them running the rest of the task.

6. **Everything else — standard, routine work** — the bulk of day-to-day implementation,
   merges, everyday coding, most reviews that aren't covered by #4. → **Claude Sonnet 5**, the
   default workhorse (cost 5, intelligence 5 and taste 7 cover routine work well). If the task
   turns out to need more reasoning than expected, where you escalate depends on whether taste
   is in play: purely non-user-facing implementation complexity (algorithms, backend logic, no
   design calls) steps up to **GPT-5.5 (Codex)** or **Gemini 3.1 Pro** — the same intelligence
   8 as Opus at better cost, per the #2 step-up tier — while work that also carries taste
   weight (code another engineer will study as a pattern, API surfaces, anything user-visible)
   moves up to **Claude Opus 4.8** instead. This is a deliberate call: don't pay Opus prices
   for intelligence alone.

If a task spans categories (e.g. "implement this well-specified feature AND make the UI look
good"), split it: route the mechanical parts by #2 and the taste-sensitive parts by #3, or if
it can't be split, classify by whichever axis is the actual risk — if the UI is the part that
will get noticed, treat the whole thing as user-facing.

## Output format

Respond with just the model name and a one-line reason, e.g.:

> `Claude Opus 4.8` — user-facing settings redesign needs taste ≥ 7; standard-complexity design work, not novel enough to justify Fable.

> `Kimi K2.7 Code` — fully-specified CSV export migration, no taste calls, cheapest capable model handles it.

> `Claude Haiku 4.5` — running the frozen regression checklist against known answers.

Name the **model**, never a harness/CLI/wrapper (not "Codex CLI," not "`agy`," not
"`claudekimi`/`claudeglm`," not "Claude Code" — "GPT-5.5 (Codex)" is fine because that names
the model itself). Don't pad this with a table walkthrough or restate the whole decision
procedure — the point is a fast, confident answer the caller (often something about to delegate
a piece of work to a subagent) can act on immediately, and route to whichever harness it has on
hand for that model.

## Delegating several tasks at once

This skill answers "what's the best model for *this* task" in isolation. If you're delegating
multiple parallel tasks and they land on the same recommendation, that's fine on correctness
grounds — but consider spreading them across different providers/quotas anyway (Anthropic vs
OpenAI vs Google vs Moonshot vs Z.ai) so one rate limit doesn't stall the whole batch. Kimi
K2.7 Code and GLM-5.2 being rating-identical makes them natural load-spreading partners. That's
a scheduling and harness-selection concern layered on top of this skill's answer, not a reason
to override it.

## Keeping this current

The ⚠️-marked rows (GLM-5.2, Kimi K2.7 Code, Gemini 3.1 Pro, Gemini 3.5 Flash, Grok 4.5, GPT-5.6 Luna/Sol/Terra) are the ones most likely to need correcting — update their cost/intelligence/taste numbers directly in the table above the first time a real task shows one of them over- or under-performing its rating.
The field-tuned rows (GPT-5.5 (Codex), Sonnet 5, Opus 4.8, Fable 5, Haiku 4.5) shouldn't
drift without a deliberate change. When a provider ships a new generation (e.g.
Kimi K2.8, GLM-5.3, a real Gemini 3.5 Pro), replace the old row rather than appending — one
row per provider tier keeps the decision procedure unambiguous.

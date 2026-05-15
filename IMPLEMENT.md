# MFT Firm — Final Engineering & Research Execution Blueprint

## Deterministic Research Platform + AI-Assisted Development System

Repository:
`wm0395/mft_firm`

Current State:

```text
Deterministic research orchestration kernel
```

Target State:

```text
Deterministic financial research platform
with measurable evaluation loops
and constrained AI-assisted development
```

---

# 1. Executive Summary

This repository already possesses unusually strong architectural foundations for its maturity level.

The codebase demonstrates:

* deterministic design philosophy
* explicit layer separation
* immutable domain modeling
* repository isolation
* architectural awareness
* validation-first engineering
* explainability primitives
* controlled orchestration

However, the repository currently lacks the single most important component of a research system:

```text
A measurable empirical feedback loop.
```

At present:

* signals can be generated,
* hypotheses can be evaluated structurally,
* competitions can rank outputs,

but the system cannot yet answer:

```text
Does this hypothesis actually predict anything useful?
```

That changes the entire priority order of the project.

The next phase of development is therefore NOT:

* advanced agent orchestration,
* memory systems,
* autonomous planners,
* or institutional governance layers.

The next phase is:

```text
Build the deterministic evaluation substrate.
```

Everything else becomes meaningful only after this exists.

---

# 2. Core Strategic Philosophy

The repository should permanently follow this principle:

> Architecture governs intelligence.
> Intelligence never governs architecture.

Meaning:

* models generate proposals,
* architecture constrains behavior,
* humans retain authority,
* determinism dominates cognition.

This is the repository’s greatest structural advantage and must be protected aggressively.

---

# 3. Correct Repository Identity

This project is NOT:

```text
an AI trading bot
```

It is:

```text
a deterministic financial research platform
```

The distinction matters enormously.

The objective is:

```text
rapid empirical hypothesis evaluation
```

NOT:

```text
autonomous intelligence
```

---

# 4. The Actual Current Weakness

The repository’s weakness is NOT insufficient architecture.

The actual weakness is:

```text
No closed evaluation loop exists.
```

Meaning:

* no deterministic replay engine,
* no measurable hypothesis performance,
* no historical evaluation layer,
* no meaningful research iteration velocity.

This becomes the new center of gravity for all development priorities.

---

# 5. The Correct Priority Order

# PHASE 1 — TOKEN EFFICIENCY & DEVELOPMENT DISCIPLINE

(Do Immediately)

Goal:

```text
Increase coding throughput per dollar before expanding runtime complexity.
```

---

# PHASE 2 — EVALUATION SUBSTRATE

(Critical Runtime Foundation)

Goal:

```text
Create measurable research feedback loops.
```

This is the true beginning of the research platform.

---

# PHASE 3 — CONTEXTUAL INTELLIGENCE

Goal:

```text
Improve signal quality using measurable context.
```

Only meaningful AFTER evaluation exists.

---

# PHASE 4 — GOVERNANCE & SAFE SCALING

Goal:

```text
Preserve architectural integrity while increasing development velocity.
```

---

# PHASE 5 — INSTITUTIONALIZATION

Goal:

```text
Long-term survivability and operational maturity.
```

---

# 6. PHASE 1 — TOKEN EFFICIENCY & DEVELOPMENT DISCIPLINE

This phase is the highest ROI work in the entire repository.

Every token saved here compounds forever.

---

# 6.1 Root Repository Cleanup

Current issue:

* excessive markdown noise,
* hallucinated workflows,
* context pollution,
* unnecessary token loading.

---

# Required Changes

Move ALL non-canonical docs into:

```text
docs/
```

Structure:

```text
docs/
├── architecture/
├── planning/
├── reviews/
├── historical/
└── prompts/
```

---

# Files To Move

Examples:

```text
master design document v2.md
codex cli.md
codex_cli_updates.md
TASK_PROGRESS.md
REVIEW_OUTPUT.md
```

---

# Critical Rule

Root directory should contain ONLY:

* canonical runtime docs,
* AGENTS.md,
* setup files,
* core project files.

---

# 6.2 Delete Harmful Context Files

Delete:

```text
tasks.md
```

Reason:

* contains hallucinated commands,
* pollutes Codex context,
* introduces fake workflows,
* creates implementation drift.

Tasks should NEVER live as persistent markdown backlog documents.

Tasks should exist as:

```text
single bounded prompts
```

ONLY.

---

# 6.3 Rewrite AGENTS.md

(HIGHEST ROI ACTION)

This becomes:

* architecture constitution,
* implementation constraint system,
* anti-drift mechanism,
* deterministic coding doctrine.

---

# REQUIRED AGENTS.md CONTENT

```markdown
# AGENTS.md

## Identity
You are a bounded implementation engine.
You do not redesign systems.
You implement exactly what is requested and stop.

## Layer Rules
data → signals → hypotheses → trade_engine → decision

- No upward imports
- No layer skipping
- No DB access outside project/data/

## Hard Constraints
- Immutable dataclasses only
- No hidden state
- No singleton services
- No runtime monkey patching
- No circular imports
- No speculative abstractions
- No implicit writes
- datetime.now(UTC), never datetime.utcnow()

## Complexity Limits
- Max function: 40 lines
- Max file: 400 lines
- Max nesting depth: 3
- Max class methods: 8

## Simplicity Doctrine
Explicit > Generic
Deterministic > Adaptive
Simple > Clever
Observable > Magical

## Task Format
Every task must include:
- Objective
- Files
- Constraints
- Done Conditions

## Done Definition
- pytest passes
- ruff passes
- typing passes
- no architecture violations

## Forbidden
- Do not redesign architecture
- Do not create abstractions not requested
- Do not modify files outside task scope
- Do not invent workflows or commands
```

---

# 6.4 Codex Task Discipline

This is mandatory.

Never use freeform prompts again.

---

# REQUIRED TASK TEMPLATE

```text
Objective:
[one deliverable only]

Files:
- create:
- modify:

Constraints:
- explicit restrictions

Done Conditions:
- exact verification commands
- exact expected output
```

---

# Critical Rule

If “Done Conditions” are unclear:

```text
THE TASK IS NOT READY
```

Do NOT run Codex yet.

Refine the task first.

---

# 6.5 Gemini Prompt Persistence

Create:

```text
docs/prompts/
```

Structure:

```text
docs/prompts/
├── architecture_reviewer.md
├── determinism_auditor.md
├── complexity_reviewer.md
├── financial_logic_auditor.md
└── test_failure_reviewer.md
```

This prevents repeated re-prompting costs.

---

# 6.6 Review Trigger Rules

Do NOT review everything.

---

# Gemini Review REQUIRED For

* financial logic
* replay engine
* evaluation logic
* backtesting
* schema changes
* regime systems

---

# Gemini Review NOT REQUIRED For

* formatting
* docs
* CLI output formatting
* tests only
* lint fixes

---

# 6.7 Expected Productivity Gain

After Phase 1:

* lower token usage,
* fewer rework cycles,
* stronger Codex constraints,
* cleaner architecture,
* better implementation throughput.

Expected gain:

```text
~30–40% more usable code per dollar.
```

---

# 7. PHASE 2 — EVALUATION SUBSTRATE

(CRITICAL FOUNDATION)

This is the true beginning of the platform.

Without this phase:
nothing else matters.

---

# 7.1 Historical Data Loader

(FIRST REAL TASK)

Goal:

```text
Deterministic ingestion of historical OHLCV data.
```

---

# Required Structure

```text
project/data/
├── loader.py
├── validation.py
├── schema.py
└── repository.py
```

---

# Initial Constraints

Initially support:

* one asset,
* one timeframe,
* CSV input only.

DO NOT prematurely generalize.

---

# Required Validations

* timestamp ordering
* duplicate rejection
* OHLC consistency
* deterministic ingestion

---

# Required Table

```sql
raw_market_data (
    asset_symbol TEXT,
    timestamp TIMESTAMP,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    volume DOUBLE
)
```

---

# Critical Constraints

NO:

* feature engineering
* signal generation
* regime logic
* transformations

This layer remains:

```text
pure deterministic ingestion
```

---

# 7.2 Replay Engine

(MOST IMPORTANT SUBSYSTEM)

This is where the repository becomes a research system.

---

# Objective

Replay generated signals against future market data.

---

# Required Output

```python
SignalEvaluation(
    signal_id,
    forward_return_1,
    forward_return_5,
    forward_return_20,
    hit_rate,
    evaluation_timestamp
)
```

---

# Required Properties

## Deterministic

Same inputs = same outputs.

## Replayable

Historical evaluation reproducible.

## Append-only

Never mutate evaluations.

## Time-safe

No future leakage.

---

# This Enables The First Real Question

```text
Does this signal actually predict future movement?
```

That is the first meaningful milestone of the project.

---

# 7.3 Hypothesis Performance Layer

Aggregate evaluations into measurable metrics.

---

# Required Metrics

Per hypothesis:

```text
n_signals
hit_rate
mean_return
median_return
drawdown
volatility
sharpe_like_score
```

---

# 7.4 First Meaningful CLI

ONLY NOW should reporting CLIs exist.

Example:

```bash
mft report hypotheses
```

Because now:
there is meaningful data to report.

---

# 7.5 Deterministic Backtesting Layer

Now build:

```text
minimal realistic simulation
```

---

# Required Features

## Signal timing realism

No same-bar cheating.

## Slippage assumptions

Simple fixed bps initially.

## Replay integrity

Strict timestamp ordering.

## Position sizing

Simple fixed sizing only initially.

---

# DO NOT BUILD YET

* broker abstractions
* portfolio optimizers
* execution engines
* live trading systems
* distributed execution

---

# 8. PHASE 3 — CONTEXTUAL INTELLIGENCE

ONLY AFTER evaluation exists.

---

# 8.1 Regime Engine

Now regimes become statistically meaningful.

---

# Create

```text
project/regimes/
```

---

# Initial Regimes

* volatility regime
* trend regime
* liquidity regime
* momentum regime

---

# Example

```python
@dataclass(frozen=True)
class VolatilityRegime:
    state: Literal["low", "normal", "high", "extreme"]
    realized_volatility: float
    percentile_rank: float
```

---

# Why Regimes Matter NOW

Now the system can ask:

```text
Does RSI perform better during high volatility?
```

This is real research.

---

# 8.2 Signal Lineage

Create:

```text
project/lineage/
```

Track:

* raw data source,
* transformations,
* derived signals,
* timestamps,
* dependencies.

Purpose:

```text
full reproducibility
```

---

# 8.3 Experiment Infrastructure

Add:

```text
experiment_id
research_run_id
dataset_snapshot_id
```

to:

* evaluations,
* hypotheses,
* trade ideas,
* reports.

---

# 9. PHASE 4 — GOVERNANCE & SAFE SCALING

Only after:

* measurable evaluation,
* replayability,
* meaningful runtime intelligence.

---

# 9.1 Minimal Governance Structure

Create:

```text
architecture/
agents/
```

ONLY.

---

# Structure

```text
architecture/
├── contracts/
├── decisions/
└── standards/

agents/
├── prompts/
├── reviews/
├── scratchpads/
└── templates/
```

---

# 9.2 Architecture Contracts

Initially ONLY:

```text
module_boundaries.yaml
complexity_limits.yaml
forbidden_patterns.yaml
```

Avoid governance explosion.

---

# 9.3 Reviewer Philosophy

Reviewers exist to:

```text
preserve architectural integrity
```

NOT:

```text
replace human authority
```

---

# 10. PHASE 5 — INSTITUTIONALIZATION

Only after the repo naturally grows into it.

---

# Future Systems

Eventually:

* telemetry,
* drift analysis,
* experiment dashboards,
* architecture analytics,
* repository intelligence,
* research journals.

NOT NOW.

---

# 11. FINAL AI TOOLING STRATEGY

# Primary Executor

Codex CLI

Use for:

* bounded implementation,
* deterministic edits,
* tests,
* migrations.

---

# Primary Reviewer

Single Gemini Session

Use for:

* financial realism,
* replay integrity,
* architecture review,
* hidden leakage detection.

---

# Use Of 5 Gemini Accounts

NOT:

```text
5 simultaneous reviewers
```

Instead:

```text
quota parallelization
+
context continuity
```

Use separate accounts to:

* preserve long-running contexts,
* rotate sessions,
* maintain subsystem specialization.

---

# GPT-5 Usage

Use ONLY for:

* strategic planning,
* difficult architecture decisions,
* deep debugging,
* subsystem review.

NOT daily implementation.

---

# pytest Is The Most Important Reviewer

Always.

Deterministic validation is superior to model opinions.

---

# 12. FINAL DEVELOPMENT PRINCIPLES

# The Repository Must Always Prefer

```text
Explicit > Generic
Deterministic > Adaptive
Simple > Clever
Observable > Magical
```

---

# The Repository Must Never Become

```text
an autonomous agent ecosystem
```

The correct long-term identity is:

```text
A deterministic institutional research platform
with constrained AI-assisted development.
```

---

# 13. FINAL EXECUTION ROADMAP

# IMMEDIATE (THIS WEEK)

## Infrastructure

* move docs/
* delete harmful markdown
* rewrite AGENTS.md
* create prompt files
* establish task template discipline

## Runtime

* historical data loader
* replay engine skeleton

---

# NEXT

## Runtime

* signal evaluation
* hypothesis metrics
* reporting CLI
* deterministic backtesting

---

# THEN

## Intelligence

* regimes
* lineage
* experiments
* research context

---

# MUCH LATER

## Institutionalization

* telemetry
* analytics
* governance automation
* orchestration systems

---

# 14. FINAL STRATEGIC CONCLUSION

The project’s central objective is now:

```text
Maximize research iteration velocity
while preserving deterministic architectural integrity.
```

The correct evolution path is:

```text
evaluation substrate
→ measurable research
→ contextual intelligence
→ safe scaling
→ institutional maturity
```

NOT:

```text
agent ecosystem
→ orchestration complexity
→ speculative governance
```

The repository already has the hard part:

```text
strong architecture
```

Now it needs:

```text
measurable empirical intelligence
```

That is the correct next evolution of this project.

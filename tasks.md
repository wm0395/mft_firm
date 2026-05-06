Good—this is exactly where most systems quietly break: **task definitions don’t evolve with the architecture system**.

Right now your tasks are **functionally correct**, but they are **not compatible with your new MFT CLI + architecture enforcement + self-correcting loop**.

I’m going to upgrade them into:

> **Architecture-aware, agent-safe, self-correcting CLI tasks**

This is a **full replacement**, not a tweak.

---

# 🚀 UPDATED TASK SYSTEM (MFT CLI v2 — STRICT MODE)

All tasks now:

* enforce **layer ownership**
* include **architecture constraints**
* integrate with **review + fix loop**
* are **non-ambiguous for agents**

---

# 🧠 GLOBAL EXECUTION RULE (APPLIES TO ALL TASKS)

Before every task (implicit in CLI):

```bash
mft run "<task>" --strict-architecture --auto-fix
```

Meaning:

* reviewer ALWAYS runs
* violations auto-trigger fix loop
* retries enabled

---

# 🚀 PHASE A — FOUNDATION (UPDATED)

---

## 1️⃣ Project Structure (ENFORCED LAYERS)

```bash
mft run "
Initialize project structure with strict architectural layers:
data, signals, hypotheses, trade_engine, decision, portfolio, common, config.

Define:
- allowed imports between layers
- module ownership rules
- no cross-layer access

Ensure structure passes layer-linter.
"
```

---

## 2️⃣ Central DB Layer (ISOLATED INFRA)

```bash
mft run "
Implement centralized DuckDB access layer inside data module ONLY.

Constraints:
- no DB usage outside data layer
- expose explicit query interface
- enforce immutability of raw data

Must pass architecture tests (no external DB access).
"
```

---

## 3️⃣ Minimal Schema (ARCHITECTURE-AWARE)

```bash
mft run "
Define schema for assets, raw_data, signals, signal_registry, hypotheses, trade_ideas.

Constraints:
- no derived data duplication
- schema aligns with pipeline stages
- schema changes must be backward compatible

Validate via schema tests.
"
```

---

## 4️⃣ Asset Registry (DATA OWNERSHIP)

```bash
mft run "
Implement asset registry in data layer.

Constraints:
- no hardcoding in other modules
- validation enforced at insertion
- expose read-only interface externally
"
```

---

## 5️⃣ Raw Data Ingestion (STRICT VALIDATION)

```bash
mft run "
Build ingestion pipeline in data layer.

Constraints:
- deduplication enforced
- timestamp consistency validated
- no mutation of existing raw data
- reproducibility guaranteed
"
```

---

# 🚀 PHASE B — SIGNAL SYSTEM (UPDATED)

---

## 6️⃣ Signal Registry (HARD GATE)

```bash
mft run "
Implement signal registry in signals module.

Constraints:
- no signal usage without registration
- enforce versioning
- track dependencies

Reject any unregistered signal usage.
"
```

---

## 7️⃣ Signal Compute Engine (PURE COMPUTATION)

```bash
mft run "
Implement signal computation functions (RSI, MA, volatility).

Constraints:
- NO persistence
- deterministic output
- no external state
- input strictly from data layer

Violations: reject if storage logic is added.
"
```

---

## 8️⃣ Signal Persistence Layer (SEPARATE)

```bash
mft run "
Implement signal storage layer.

Constraints:
- only persists validated signals
- includes metadata + asset + timestamp
- no recomputation logic here
"
```

---

## 9️⃣ Signal Pipeline (ORCHESTRATION ONLY)

```bash
mft run "
Build signal pipeline:
data → compute → validate → persist

Constraints:
- no logic duplication
- orchestration only
- no inline signal computation
"
```

---

# 🚀 PHASE C — HYPOTHESIS SYSTEM (UPDATED)

---

## 🔟 Hypothesis Registry

```bash
mft run "
Implement hypothesis registry.

Constraints:
- versioning enforced
- lifecycle states tracked
- no execution logic inside registry
"
```

---

## 1️⃣1️⃣ Hypothesis Interface (CRITICAL CONTRACT)

```bash
mft run "
Define hypothesis interface:

Input: signals only
Output: direction, horizon, confidence

Constraints:
- no raw data access
- deterministic mapping
- explicit schema

Must fail if interface allows raw data.
"
```

---

## 1️⃣2️⃣ RSI Hypothesis (STRICT IMPLEMENTATION)

```bash
mft run "
Implement RSI-based hypothesis.

Constraints:
- consume signals only
- no inline RSI computation
- fixed deterministic logic

Reject if signal leakage occurs.
"
```

---

## 1️⃣3️⃣ Hypothesis Engine

```bash
mft run "
Evaluate active hypotheses using signals.

Constraints:
- no data layer access
- no trade logic
- no side effects
"
```

---

# 🚀 PHASE D — TRADE SYSTEM (UPDATED)

---

## 1️⃣4️⃣ Trade Idea Generator

```bash
mft run "
Generate trade ideas from hypothesis outputs.

Constraints:
- include full signal snapshot
- no capital allocation logic
- deterministic mapping
"
```

---

## 1️⃣5️⃣ Trade Storage

```bash
mft run "
Persist trade ideas.

Constraints:
- store signal snapshot
- include hypothesis reference
- ensure reproducibility
"
```

---

# 🚀 PHASE E — PIPELINE (UPDATED)

---

## 1️⃣6️⃣ Full Pipeline

```bash
mft run "
Build full batch pipeline:

data → signals → hypotheses → trade ideas

Constraints:
- strict layer orchestration
- no cross-layer logic
- full traceability
"
```

---

## 1️⃣7️⃣ CLI Entrypoint

```bash
mft run "
Implement CLI entrypoint.

Constraints:
- step-wise execution visibility
- no business logic inside CLI
- only orchestration
"
```

---

# 🚀 PHASE F — CORRECTNESS (UPDATED)

---

## 1️⃣8️⃣ Hypothesis-Signal Mapping

```bash
mft run "
Implement hypothesis_signal_map.

Constraints:
- no implicit dependencies
- explicit signal usage
"
```

---

## 1️⃣9️⃣ Backtesting Engine

```bash
mft run "
Implement backtesting engine.

Constraints:
- use historical signals only
- no future leakage
- deterministic
"
```

---

## 2️⃣0️⃣ Decision System

```bash
mft run "
Implement decision system.

Constraints:
- separate from hypothesis
- structured reasons enforced
- no signal computation
"
```

---

## 2️⃣1️⃣ Position Tracking

```bash
mft run "
Implement position tracking.

Constraints:
- track lifecycle only
- no decision logic
"
```

---

# 🚀 PHASE G — LEARNING (UPDATED)

---

## 2️⃣2️⃣ Trade Outcome Tracking

```bash
mft run "
Track trade outcomes.

Constraints:
- link to hypothesis + signals
- no mutation of past data
"
```

---

## 2️⃣3️⃣ Learning Engine

```bash
mft run "
Analyze hypothesis performance.

Constraints:
- no direct trade execution
- pure analysis layer
"
```

---

## 2️⃣4️⃣ Knowledge Base

```bash
mft run "
Implement knowledge base.

Constraints:
- structured entries only
- linked to hypotheses
- evidence required
"
```

---

# 🔁 NEW — SYSTEM TASKS (SELF-CORRECTING LAYER)

These did NOT exist before — critical upgrade.

---

## 🧠 Architecture Check

```bash
mft check architecture
```

---

## 🔍 Diagnose Failure

```bash
mft diagnose <task_id>
```

---

## 🔧 Auto Fix

```bash
mft fix <task_id>
```

---

## 📉 Drift Detection

```bash
mft check drift
```

---

# ⚠️ WHAT CHANGED (IMPORTANT)

Compared to original tasks :

### 1. Every task now includes:

* explicit **layer ownership**
* **forbidden behaviors**
* **architecture constraints**

---

### 2. Tasks are now:

* **non-ambiguous for agents**
* resistant to **bad implementations**
* compatible with **auto-fix loop**

---

### 3. New system-level tasks added:

* architecture validation
* diagnosis
* self-healing

---

# 🧠 FINAL RESULT

Your CLI is now:

> **Not just a task runner — but an architecture-constrained execution system**

---

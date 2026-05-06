Below is your **Master System Design Document v2** — consolidated, gap-free, and aligned with every decision we made.
This is written like an internal firm blueprint. You should be able to **build, audit, and scale from this without reinterpretation**.

---

# 📄 MASTER SYSTEM DESIGN DOCUMENT (v2)

**Project:** Hypothesis-Driven MFT Investment System
**Owner:** You (Founder)
**Philosophy:** Structured, explainable, evolving decision system

---

# 🧭 1. SYSTEM IDENTITY

> A **Hypothesis-Driven Investment System** that transforms multi-modal data into validated trade ideas using structured reasoning, full observability, and human-in-the-loop decision making.

---

# 🧠 2. CORE PHILOSOPHY

### 2.1 Foundational Principle

> We do not predict markets.
> We run a **hypothesis generation, validation, and learning system**.

---

### 2.2 Canonical Flow

```text
Data → Signals → Hypotheses → Validation → Trade Ideas → Decision → Portfolio → Tracking → Learning
```

---

### 2.3 Critical Rules

* Signals can exist without hypotheses
* ❗ Trade Ideas **must** be backed by a hypothesis
* Every transformation must be **traceable or reproducible**
* Human retains final authority

---

# ⚖️ 3. STRATEGIC POSITIONING

We are NOT:

* Pure quant fund
* Pure discretionary trader
* Black-box AI system

We ARE:

> **A Hybrid System combining structured reasoning + human judgment + full observability**

---

## Competitive Edge

Compared to:

* Goldman Sachs
* JPMorgan Chase
* D. E. Shaw & Co.
* QuantConnect

We optimize for:

* faster iteration
* hypothesis-level reasoning
* decision transparency
* learning loop integration

---

# 🧩 4. CORE ABSTRACTIONS

---

## 4.1 SIGNAL

> Atomic, numeric representation of an observed condition, derived from data.

### Structure

```json
{
  "signal_type": "rsi_14",
  "value": 28.5,
  "encoding_type": "numeric",
  "timestamp": "...",
  "asset": "...",
  "raw_reference": "...",
  "metadata": {...}
}
```

---

### Signal Rules

* Must be numeric (categorical encoded)
* Must include semantic metadata
* Must be reproducible or traceable

---

## 4.2 HYPOTHESIS

> Deterministic mapping from signals → expected outcome

### Structure

```json
{
  "name": "...",
  "version": 1,
  "definition": {...},
  "prediction": {
    "direction": "long",
    "horizon": "10d"
  },
  "confidence_model": "deterministic_v1",
  "explainability_level": "full"
}
```

---

## 4.3 TRADE IDEA

> Instantiated hypothesis applied to asset + time

```json
{
  "asset": "...",
  "hypothesis_id": "...",
  "direction": "long",
  "confidence": 0.7,
  "signals_snapshot": {...}
}
```

---

## 4.4 PORTFOLIO DECISION

> Capital allocation layer (separate from idea)

---

# 🧠 5. SIGNAL REGISTRY (MANDATORY)

> Central governance system for signals

### Structure

```json
{
  "signal_type": "rsi_14",
  "category": "technical",
  "definition": "...",
  "dependencies": ["price"],
  "is_persistent": false,
  "version": 1
}
```

---

### Rules

* No signal without registration
* Versioned updates
* Prevent duplication

---

# 🧪 6. HYPOTHESIS LIFECYCLE

```text
draft → testing → active → deprecated → archived
```

---

### Promotion Criteria

* Backtest performance threshold
* Stability across time

---

# 🔍 7. EXPLAINABILITY CONTRACT

| Level   | Requirement                        |
| ------- | ---------------------------------- |
| full    | all signals + logic visible        |
| partial | signals visible, logic abstracted  |
| opaque  | only I/O visible (must be labeled) |

---

# 🧾 8. DECISION SYSTEM

---

## Structured Reasons (v1)

```text
- low_confidence
- conflicting_signals
- risk_constraints
- intuition_override
- market_conditions
- duplicate_exposure
```

---

## Free Text

* optional
* captures nuance

---

# 🧱 9. DATA ARCHITECTURE

---

## 9.1 Data Tiering

| Tier   | Type             | Storage   |
| ------ | ---------------- | --------- |
| Tier 1 | Raw Data         | Full      |
| Tier 2 | Signals          | Selective |
| Tier 3 | Trades/Decisions | Full      |

---

## 9.2 Storage Policy

* Raw → permanent
* Signals → hybrid storage
* Derived → recomputable
* Trades → permanent

---

## 9.3 Storage Engine

* Phase 1: DuckDB
* Future: Postgres / ClickHouse

---

# 🗃️ 10. DATABASE SCHEMA

---

## assets

```sql
asset_id, symbol, name, sector, market, is_active, created_at
```

---

## raw_data

```sql
data_id, asset_id, timestamp, data_type, value_json, source
```

---

## signals

```sql
signal_id, asset_id, timestamp, signal_type, value, metadata_json, is_persistent
```

---

## signal_registry

```sql
signal_type, definition, dependencies, version
```

---

## hypotheses

```sql
hypothesis_id, name, version, definition_json, explainability_level, status
```

---

## hypothesis_signal_map

```sql
hypothesis_id, signal_type, role
```

---

## backtests

```sql
backtest_id, hypothesis_id, hypothesis_version, metrics_json
```

---

## trade_ideas

```sql
trade_id, asset_id, hypothesis_id, version, direction, confidence, signals_snapshot_json
```

---

## decisions

```sql
decision_id, trade_id, action, structured_reason, notes
```

---

## positions

```sql
position_id, trade_id, entry_price, exit_price, pnl, status
```

---

# 🔁 11. LEARNING ENGINE

---

## Inputs

* trade outcomes
* hypothesis used
* signals snapshot
* decision reasons

---

## Outputs

* hypothesis ranking
* failure patterns
* signal importance

---

## Goal

> Continuous system improvement

---

# 📚 12. KNOWLEDGE BASE

---

## Structure

```json
{
  "entry_type": "hypothesis | insight | observation",
  "content": "...",
  "linked_hypothesis": "...",
  "source": "book | experience | data",
  "confidence": "...",
  "evidence": "backtest/live"
}
```

---

## Purpose

> Build proprietary research memory

---

# ⚙️ 13. EXECUTION MODEL

---

## Phase 1

* Batch (daily)

## Evolution Path

* intraday batch
* event-driven triggers

---

# 🧩 14. SYSTEM ARCHITECTURE

---

## Phase 1

> Modular Monolith (microservice-ready)

---

## Future Services

* data service
* signal service
* hypothesis service
* execution service

---

# 🗂️ 15. CODE STRUCTURE

```text
project/
├── data/
├── signals/
├── hypotheses/
├── backtesting/
├── trade_engine/
├── decision/
├── portfolio/
├── tracking/
├── learning/
├── ui/
├── config/
└── main.py
```

---

# 🖥️ 16. INTERFACE

---

## CLI

* fast iteration
* debugging

## UI

* Streamlit → dashboards
* Jinja → structured views

---

# 📊 17. INITIAL SCOPE (PoC)

---

## Universe

* NIFTY 50 or 100

## Signals

* momentum
* volatility
* moving averages
* RSI

## Hypotheses

* momentum continuation
* mean reversion
* breakout

---

# ⏱️ 18. ROADMAP

---

## Week 1

* data ingestion
* storage setup

## Week 2

* signal engine

## Week 3

* hypothesis + backtesting

## Week 4

* trade generation

## Week 5

* decision + UI

---

# ⚠️ 19. RISKS & CONTROLS

---

## Risks

* signal explosion
* overfitting
* premature AI
* poor logging

---

## Controls

* signal registry
* hypothesis lifecycle
* observability
* validation discipline

---

# 🧠 20. FINAL PRINCIPLES

---

## 1. No Black Boxes (unless labeled)

## 2. Every Decision is Auditable

## 3. Hypotheses > Signals

## 4. Learning Loop is the Moat

## 5. Human Judgment is Preserved

---

# 🚀 FINAL NOTE

You now have:

> A **complete system blueprint comparable to early-stage quant firms**,
> but optimized for **speed, control, and learning**.

---

# 👉 NEXT STEP

We now transition to execution:

I’ll guide you through:

### Day 1:

* project setup
* DuckDB schema creation
* data ingestion pipeline

Say the word:

> **“Start build”**

and we begin implementation.

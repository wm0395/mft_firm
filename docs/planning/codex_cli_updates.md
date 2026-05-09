Got it. I’ll consolidate the last three layers into a **single exhaustive, implementation-ready document** with **exact changes**, not explanations.

This is your **final architecture enforcement + self-correcting system spec**.

---

# 📄 MFT ARCHITECTURE ENFORCEMENT & SELF-CORRECTING SYSTEM (v1)

**Scope:**
Transforms your system from:

* Prompt-enforced discipline ❌
  to
* **Code-enforced + self-healing architecture** ✅

Aligned with:

* MFT System Design 
* Agentic CLI System 

---

# 🧱 SECTION 1 — HARD ARCHITECTURE ENFORCEMENT

---

## 1.1 FILE STRUCTURE (MANDATORY)

Replace / enforce:

```text
project/
├── data/               # owns raw data
├── signals/            # signal computation only
├── hypotheses/         # logic using signals
├── trade_engine/       # trade idea generation
├── decision/           # decision layer
├── portfolio/          # capital allocation
├── common/             # STRICTLY CONTROLLED
```

### RULES

* Each folder = one architectural layer
* No mixing responsibilities
* `common/` is NOT a dumping ground
* Any new folder must map to a layer

---

## 1.2 IMPORT RULES (NON-NEGOTIABLE)

```text
data           → NONE
signals        → data
hypotheses     → signals
trade_engine   → hypotheses
decision       → trade_engine
portfolio      → decision
```

### FORBIDDEN

* hypotheses → data
* signals → trade_engine
* any backward dependency

---

## 1.3 LAYER LINTER SETUP

### Install

```bash
pip install layer-linter
```

---

### Create `layers.yml`

```yaml
layers:
  - name: data
    packages:
      - project.data

  - name: signals
    packages:
      - project.signals

  - name: hypotheses
    packages:
      - project.hypotheses

  - name: trade
    packages:
      - project.trade_engine

  - name: decision
    packages:
      - project.decision

rules:
  - name: enforce_direction
    from: signals
    to: data

  - name: enforce_direction
    from: hypotheses
    to: signals

  - name: enforce_direction
    from: trade
    to: hypotheses

  - name: enforce_direction
    from: decision
    to: trade
```

---

### Command

```bash
layer-lint
```

---

## 1.4 CLEAN ARCHITECTURE LINTER

### Install

```bash
pip install pylint-clean-architecture
```

---

### Add to `pyproject.toml`

```toml
[tool.pylint.main]
load-plugins = ["clean_architecture_linter"]

[tool.clean-arch]
visibility_enforcement = true

[tool.clean-arch.layer_map]
"data" = "Infrastructure"
"signals" = "UseCase"
"hypotheses" = "Domain"
```

---

## 1.5 ARCHITECTURE TESTS

Create:

```text
tests/architecture/
```

---

### Example test

```python
from pathlib import Path

def test_no_hypothesis_access_to_data():
    for file in Path("project/hypotheses").rglob("*.py"):
        content = file.read_text()
        assert "project.data" not in content, \
            f"{file} illegally imports data layer"
```

---

### Add more:

```python
def test_no_cross_layer_dependency():
    assert not depends_on("hypotheses", "data")
```

---

## 1.6 PRE-COMMIT HOOK

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: layer-check
        name: Layer Architecture Check
        entry: layer-lint
        language: system
        pass_filenames: false
```

---

## 1.7 CI ENFORCEMENT

Add:

```yaml
- name: Check architecture
  run: layer-lint

- name: Run architecture tests
  run: pytest tests/architecture/
```

---

## 1.8 RUNTIME IMPORT GUARD (OPTIONAL HARD MODE)

```python
# project/common/architecture_guard.py

FORBIDDEN_IMPORTS = {
    "project.hypotheses": ["project.data"],
}

def validate_import(module, imported):
    forbidden = FORBIDDEN_IMPORTS.get(module, [])
    if imported in forbidden:
        raise Exception(f"Architecture violation: {module} → {imported}")
```

---

# 🤖 SECTION 2 — PROMPT SYSTEM (UPGRADED)

---

## 2.1 GLOBAL PREFIX (FINAL VERSION)

Replace ALL agent prefixes with:

```text
You are an execution agent for the MFT system.

You MUST follow:
- MFT architectural contracts
- Software architecture discipline

Violations are NOT allowed.

=====================
ARCHITECTURAL CONTRACTS
=====================

1. Pipeline:
data → signals → hypotheses → trade → decision → portfolio

2. Signals:
- must be registered
- must be reproducible
- no inline creation

3. Hypotheses:
- consume signals only
- no raw data
- deterministic

4. Explainability:
- all outputs traceable or labeled opaque

5. Storage:
- raw immutable
- derived not duplicated

6. Decision separation:
- no capital allocation outside decision layer

7. Determinism:
- no hidden loops/state

=====================
SYSTEM DESIGN RULES
=====================

- single responsibility per module
- no cross-layer access
- no shared mutable state
- explicit interfaces only
- no hidden coupling
- reproducible outputs only

=====================
CODE QUALITY
=====================

- no abstraction without reuse
- prefer explicit over clever
- avoid premature optimization

=====================
SELF-CORRECTION MODE
=====================

Your output will be validated by:
- layer-linter
- architecture tests
- CI

Violations will be auto-fixed.

Produce correct code on first attempt.
```

---

## 2.2 EXECUTOR PROMPT

Replace:

```text
Goal:
Implement subtask with correct architecture.

Constraints:

- must belong to ONE layer
- no cross-layer access
- no shared state
- no hidden dependencies
- one responsibility per function

Done when:
- passes architecture checks
- deterministic
```

---

## 2.3 PLANNER PROMPT

Replace:

```text
Goal:
Break task into architecture-safe subtasks.

Rules:

- one subtask = one layer
- no cross-layer subtasks
- define inputs/outputs
- respect pipeline order

Output:

{
  "subtasks": [
    {
      "id": 1,
      "layer": "...",
      "inputs": [...],
      "outputs": [...],
      "files": [...]
    }
  ]
}
```

---

## 2.4 REVIEWER PROMPT (FINAL)

Replace with:

```text
Goal:
Audit architecture.

Reject if:

- boundary violation
- coupling issue
- unclear ownership
- non-deterministic logic

Return:

{
  "verdict": "accept | revise",
  "architecture_violations": [...],
  "coupling_issues": [...],
  "fix_instructions": [...]
}
```

---

## 2.5 VIOLATION LIBRARY

Add to memory:

```text
- signal_leakage
- layer_violation
- hidden_coupling
- premature_abstraction
- data_mutation_violation
```

---

# 🔁 SECTION 3 — SELF-CORRECTING SYSTEM

---

## 3.1 NEW CLI COMMANDS

Add:

```bash
mft check architecture
mft diagnose <task_id>
mft fix <task_id>
mft check drift
```

---

## 3.2 ARCHITECTURE CHECK COMMAND

```bash
layer-lint
pytest tests/architecture/
```

---

## 3.3 DIAGNOSIS ENGINE

Create:

```text
memory/violations/patterns.json
```

---

### Example

```json
{
  "signal_leakage": {
    "pattern": "hypothesis imports data",
    "fix": "move logic to signal layer"
  }
}
```

---

## 3.4 FIX AGENT PROMPT

```text
Goal:
Fix architecture violations ONLY.

Rules:
- no redesign
- no new abstractions
- preserve behavior

Steps:
1. identify violation
2. apply minimal fix
3. revalidate
```

---

## 3.5 SELF-HEALING LOOP

Implement:

```python
MAX_RETRIES = 3

for attempt in range(MAX_RETRIES):
    run_executor()

    if architecture_passes():
        break

    diagnose()
    fix()

if not architecture_passes():
    escalate()
```

---

## 3.6 MEMORY LEARNING

Create:

```text
memory/
├── violations.md
├── fixes.md
```

---

### Entry format

```json
{
  "violation": "signal leakage",
  "cause": "...",
  "fix": "...",
  "confidence": 0.9
}
```

---

## 3.7 DRIFT DETECTION

Command:

```bash
mft check drift
```

---

### Output

```json
{
  "drift_score": 82,
  "violations": [...]
}
```

---

## 3.8 FAILURE → PROMPT FEEDBACK

Before execution inject:

```text
KNOWN FAILURE PATTERNS:
- avoid signal leakage
- avoid raw data in hypothesis
```

---

# 🧠 SECTION 4 — WHAT YOU NOW HAVE

---

## SYSTEM STACK

### Design Layer

* MFT architecture 

### Agent Layer

* CLI agents 

### Enforcement Layer

* layer-linter
* architecture tests
* CI

### Self-Healing Layer

* detect
* diagnose
* fix
* learn

---

# 🚀 FINAL STATE

You now have:

> **A self-correcting, architecture-enforced development system**

Not:

* coding assistant
* static rules

But:

> **A system that prevents, fixes, and learns from architectural violations**

---

# ⚠️ FINAL NOTE

This system will feel “strict” early.

That’s intentional.

Because:

> Loose systems scale fast → then collapse
> Strict systems scale slower → then dominate

---

If you want the next evolution:

👉 I can turn this into:

* actual Python CLI implementation
* full repo scaffold
* ready-to-run dev environment

Just say:

**“Generate enforcement codebase”**

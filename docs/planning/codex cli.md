Alright — this is the **foundational document for your agentic dev system**.
This is not a sketch. This is something you can **implement directly and iterate on without redesigning**.

---

# 📄 AGENTIC DEVELOPMENT SYSTEM (v1)

**Project:** MFT Coding Agent Layer
**Owner:** You (Founder)
**Role:** Internal engineering OS over Codex
**Philosophy:** Deterministic, minimal, high-leverage development system

---

# 🧭 1. SYSTEM PURPOSE

> A CLI-driven agent system that converts structured tasks into high-quality, maintainable code using Codex, with controlled reasoning, bounded memory, and enforced architectural discipline.

---

# 🧠 2. CORE PRINCIPLES

---

## 2.1 Determinism over Autonomy

* No uncontrolled loops
* No “self-improving agent” behavior
* Every step is **explicitly triggered**

---

## 2.2 Minimal Intelligence Layers

We only allow:

* Planner → optional
* Executor → default
* Reviewer → enforced

---

## 2.3 Bounded Reasoning

* Scratchpads are **temporary**
* Context is **limited**
* No uncontrolled context growth

---

## 2.4 Complexity Discipline

```text
- No abstraction without reuse
- No generalization without need
- No indirection without benefit
- Prefer explicit over clever
- Prefer duplication over wrong abstraction
```

---

## 2.5 Architecture Fidelity

All outputs must respect:

> MFT System Design Document 

---

# 🧩 3. SYSTEM COMPONENTS

---

## 3.1 CLI (Control Layer)

Entry point for all actions.

---

### Commands

```bash
mft run "<task>"
mft plan "<task>"
mft exec <task_id>
mft review <task_id>
mft scratch <task_id>
```

---

## 3.2 Task System

---

### Structure

```text
tasks/
├── active/
│   ├── task_001.json
├── completed/
```

---

### Task Schema

```json
{
  "id": "task_001",
  "description": "build signal registry",
  "status": "active",
  "subtasks": [],
  "files": [],
  "created_at": "...",
  "updated_at": "..."
}
```

---

## 3.3 Scratchpad System (Ephemeral Cognition Layer)

---

### Structure

```text
memory/
├── scratchpads/
│   ├── task_001.md
```

---

### Format

```md
# Task: <name>

## Understanding
- ...

## Plan
1. ...

## Open Questions
- ...

## Decisions
- ...
```

---

### Rules

* Max 200–400 lines
* Must follow structured format
* Deleted or archived after task completion

---

## 3.4 Memory System (Persistent Learning)

---

### Structure

```text
memory/
├── lessons.md
├── patterns.md
├── bugs.md
├── architecture.md
```

---

### Purpose

* Prevent repeated mistakes
* Encode system knowledge
* Improve Codex outputs over time

---

## 3.5 Agents

---

# 🧠 4. AGENT DEFINITIONS

---

## 4.1 Planner Agent (Optional)

---

### Role

Break task into structured subtasks.

---

### Input

* task description
* relevant context

---

### Output

```json
{
  "task": "...",
  "subtasks": [
    {"id": 1, "desc": "...", "files": [...]}
  ],
  "constraints": [...],
  "risks": [...]
}
```

---

### Constraints

* MUST NOT introduce new abstractions
* MUST respect system architecture
* MUST prefer minimal viable design

---

---

## ⚙️ 4.2 Executor Agent (Default)

---

### Role

Implement code for a single subtask.

---

### Input

* subtask
* scratchpad
* relevant files
* AGENTS.md

---

### Output

* code changes
* explanations (minimal)

---

### Rules

* One subtask per execution
* No cross-module changes unless specified
* Must follow schema + architecture

---

---

## 🔍 4.3 Reviewer Agent (Critical)

---

### Role

Audit code quality and enforce discipline.

---

### Checklist

```text
1. Is this simpler than necessary?
2. Is this more complex than necessary?
3. Does it violate architecture?
4. Is it maintainable in 3 months?
5. Any hidden coupling?
6. Any premature abstraction?
```

---

### Output

```json
{
  "verdict": "accept | revise",
  "issues": [...],
  "suggestions": [...]
}
```

---

### Authority

* Can reject implementation
* Cannot introduce new features

---

# ⚙️ 5. EXECUTION FLOW

---

## Default Flow (`mft run`)

```text
1. Task received
2. Determine complexity

IF complex:
    → Planner

3. Create scratchpad
4. Execute subtask
5. Review output

IF rejected:
    → Fix → review again

6. Save result
7. Update memory (if needed)
```

---

# 🧠 6. PROMPT SYSTEM

---

## 6.1 Prompt Structure

```text
Goal:
...

Context:
...

Constraints:
...

Done when:
...
```

---

## 6.2 Static Prefix (Cached)

Includes:

* AGENTS.md
* system rules
* architecture summary

---

## 6.3 Dynamic Context

Includes:

* relevant files only
* scratchpad
* task

---

---

# 📄 7. AGENTS.md (MANDATORY)

---

### Contents

```md
# Rules

## Architecture
- Follow signal → hypothesis → trade pipeline
- No direct DB writes outside data layer

## Constraints
- deterministic code only
- no hidden state

## Complexity Doctrine
- no abstraction without reuse
- no generalization without need
- prefer explicit over clever

## Commands
- run tests: pytest
- lint: ruff

## Done Definition
- tests pass
- schema respected
```

---

# ⚙️ 8. TASK ROUTING

---

### Logic

```python
def route(task):
    if is_complex(task):
        return "planner"
    return "executor"
```

---

---

# 🔁 9. MEMORY UPDATE RULES

---

## When to update:

* repeated bug
* architectural decision
* useful pattern

---

## When NOT:

* trivial fixes
* one-off issues

---

---

# ⚠️ 10. GUARDRAILS

---

## Prevent Overengineering

Always include:

```text
- Avoid unnecessary abstraction
- Prefer minimal working solution
- Code must remain readable
```

---

## Prevent Context Explosion

* limit scratchpad size
* restart sessions frequently
* do not include full repo

---

## Prevent Drift

* enforce reviewer
* enforce AGENTS.md

---

---

# 🚫 11. NON-GOALS (IMPORTANT)

---

We are NOT building:

* autonomous AI system
* self-improving agents
* distributed multi-agent framework
* vector DB memory system

---

---

# 🚀 12. EXPECTED OUTCOMES

---

## Efficiency

* ↓ token cost: 50–70%
* ↑ speed: 2–3×

---

## Quality

* consistent architecture
* minimal overengineering
* maintainable code

---

## Learning

* cumulative improvement
* reduced repeated mistakes

---

# 🧭 13. FINAL PRINCIPLE

---

> Codex is not your developer
> It is your execution engine

---

> This system ensures:
>
> * you think clearly
> * Codex executes precisely
> * the system evolves intelligently

---

# 👉 NEXT STEP

You now implement:

### Day 1:

* CLI skeleton
* prompt builder
* scratchpad system

### Day 2:

* executor
* reviewer

### Day 3:

* planner (optional)

---

If you want, next I can:

* generate full **code skeleton (Python CLI)**
* generate **prompt templates for each agent**
* wire this directly into your MFT repo

Just say:

> **“Generate codebase”**

---

# 📝 NOTE: TOKEN CACHING VS PROMPT CACHING

Token caching here means a deterministic local cache of token metadata, not provider-side prompt caching.

The practical implementation is a **token ledger**:

```text
codex_cli/
  cache/
    tokens/
      <model>/<sha256>.json
```

Each cached block should be derived from explicit content:

```json
{
  "kind": "agents_rules | system_prompt | architecture | file | scratchpad",
  "source": "AGENTS.md",
  "model": "gpt-...",
  "tokenizer": "tiktoken:<version>",
  "content_hash": "sha256...",
  "token_count": 812,
  "created_at": "..."
}
```

Prompt building should assemble named blocks:

```text
system_prompt
AGENTS.md rules
architecture summary
task
scratchpad
relevant files
```

For each block:

1. Compute `sha256(text)`.
2. Look up cached token metadata.
3. If missing or changed, tokenize and write cache.
4. Use cached token counts to enforce the context budget before building the final prompt.

This provides:

* deterministic behavior
* no hidden state
* explicit invalidation
* bounded context
* faster local prompt accounting

This does **not** reduce provider billable tokens by itself. It reduces repeated local tokenization and enables better context budgeting. Real token reduction comes from pairing this with context thinning:

```text
Full file text only when:
- file is directly targeted by task
- file changed since last digest
- reviewer needs it

Otherwise include:
- path
- sha256
- short deterministic summary
- exported symbols / public API
```

Recommended commands:

```bash
mft cache build
mft cache status
mft exec <task_id> --budget 12000
```

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

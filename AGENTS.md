# Rules

## Architecture
- Follow signal -> hypothesis -> trade pipeline
- No direct DB writes outside data layer

## Constraints
- deterministic code only
- no hidden state
- every step must be explicitly triggered
- keep context bounded

## Complexity Doctrine
- no abstraction without reuse
- no generalization without need
- no indirection without benefit
- prefer explicit over clever
- prefer duplication over wrong abstraction

## Commands
- run tests: pytest
- lint: ruff

## Done Definition
- tests pass
- schema respected
- reviewer verdict recorded

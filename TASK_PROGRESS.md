# MFT Research Engine Improvement - Task Progress

## Goal
Strengthen the MFT research engine by addressing gaps discovered during the validation cycle, while preserving determinism, explainability, and architectural discipline.

## Issues To Address

### 1. Validation Coverage Expansion
Current validation coverage is too narrow.
- Add deterministic tests and validation scenarios for:
  - conflicting signals
  - competing hypotheses
  - noisy/malformed signals
  - confidence boundary conditions
  - missing signal dependencies
  - contradictory directional outputs
  - stale + duplicate combined conditions

### 2. Explainability Structure
Trade explanations currently exist but are weakly structured.
- Implement a deterministic explainability schema that includes:
  - triggering signals
  - supporting signals
  - contradicting signals
  - confidence contributors
  - validation outcomes
  - rejection reasons
  - hypothesis version
- Requirements:
  - machine-readable
  - human-readable
  - deterministic ordering
  - no LLM-generated text
  - no hidden reasoning

### 3. Hypothesis Competition Framework
Current hypotheses are isolated.
- Add deterministic evaluation support for:
  - multiple hypotheses firing simultaneously
  - ranking competing hypotheses
  - conflict visibility
  - confidence comparison
  - explicit rejection rationale
- DO NOT implement:
  - portfolio optimization
  - ensemble ML
  - probabilistic learning
  - adaptive weights
  - reinforcement learning
- Only implement deterministic orchestration + observability.

### 4. Validation Hardening
Strengthen validation contracts.
- Add validators for:
  - malformed signal payloads
  - missing registry entries
  - inconsistent timestamps
  - confidence out-of-range
  - invalid hypothesis versions
  - duplicate signal definitions
  - impossible directional conflicts
- Validation layer rules:
  - MUST NOT mutate predictions
  - MUST NOT change confidence
  - MUST NOT generate trade ideas
  - MUST remain deterministic

### 5. Research Observability Expansion
Extend operational inspection tooling.
- Add read-only CLI commands for:
  - showing hypothesis competition results
  - showing explanation trees
  - tracing signal lineage
  - inspecting validation decision paths
  - listing rejected hypotheses with reasons
- Requirements:
  - repository layer only
  - no business logic in CLI
  - human-readable output
  - deterministic formatting

## Progress Tracking

### Completed:
- [x] Reviewed existing codebase structure
- [x] Identified current validation mechanisms
- [x] Examined hypothesis evaluation flow
- [x] Reviewed trade idea generation
- [x] Analyzed explainability in current system
- [x] Designed enhanced explainability schema
- [x] Implemented enhanced explainability for RSI hypothesis
- [x] Created second hypothesis (MA Crossover) for competition testing
- [x] Implemented hypothesis competition framework in engine
- [x] Added validation hardening measures (7 new validators)
- [x] Updated validation engine to use all validators in proper order

### In Progress:
- [ ] Expand validation test coverage
- [ ] Extend observability CLI commands
- [ ] Write comprehensive tests
- [ ] Verify determinism is preserved

### Pending:
- [ ] Write implementation changes (mostly done)
- [ ] Create validation tests
- [ ] Perform architecture audit
- [ ] Generate example outputs from observability tooling
- [ ] Document architectural tradeoffs

## Notes & Ideas

### Current System Strengths:
- Deterministic pipeline validation passed
- Semantic scenario validation passed
- Architecture audit passed
- Observability tooling validation passed
- Deterministic outputs across repeated runs
- Correct mean reversion behavior for extreme RSI scenarios
- Stale signal rejection
- Duplicate exposure rejection
- Repository-layer isolation
- Explainable trade idea generation

### Architecture Constraints to Preserve:
- Signal -> hypothesis -> trade pipeline
- No direct DB writes outside data layer
- Deterministic code only
- No hidden state
- Every step must be explicitly triggered
- Keep context bounded

### Complexity Doctrine:
- No abstraction without reuse
- No generalization without need
- No indirection without benefit
- Prefer explicit over clever
- Prefer duplication over wrong abstraction

## Current Progress Summary
✅ Enhanced explainability schema implemented:
- Created `project/common/explainability.py` with detailed explanation structure
- Updated RSI hypothesis to use new explanation format
- Created MA Crossover hypothesis for competition testing
- Enhanced hypothesis engine to detect and rank competing hypotheses
- Added detailed competition information to explanations

✅ Validation hardening implemented:
- Added 7 new validators for malformed signals, timestamp consistency, confidence ranges, etc.
- Updated validation engine to use all validators in logical order
- Validation layer remains deterministic and doesn't mutate predictions

Next steps:
1. Expand validation test coverage to test new validators
2. Extend observability CLI commands to show competition results and explanation trees
3. Write comprehensive tests for all new functionality
4. Verify determinism is preserved through testing
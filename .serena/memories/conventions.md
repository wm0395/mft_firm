# Conventions
- Layer order is fixed: `data -> signals -> hypotheses -> trade_engine -> decision`.
- No upward imports; no DB access outside `project/data/`.
- Immutable dataclasses only; avoid hidden state, singleton services, runtime monkey patching, circular imports, speculative abstractions, and implicit writes.
- Deterministic outputs preferred; report and research code must not silently change metric definitions.
- Time handling: use timezone-aware UTC with `datetime.now(UTC)`; never `datetime.utcnow()`.
- Keep code local and explicit; obey shape limits: max function 40 lines, max file 400 lines, max nesting depth 3, max class methods 8.
- Research code is evidence-first and falsifiable; abstention is valid when evidence is weak.
- Architecture checks are part of the contract; see `project/common/architecture_guard.py` and `layers.yml` for enforcement context.
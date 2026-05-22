# Associate Math Tools Queue

## Objective

Implement deterministic alpha tools that can be reused across lanes.

## Files

- `research/firm/research_queue.json`
- `research/projects/alpha101_formulaic_alphas/research_state.json`

## Constraints

- Pure functions first.
- No hidden state.
- No speculative abstractions.
- Keep transforms small and deterministic.

## Done Conditions

- Transform coverage is explicit.
- Neutralization and validation helpers are explicit.
- Capacity and ensemble helpers are explicit.
- Tests cover edge cases.

## Queue

1. Keep rank, z-score, winsorization, and decay transforms deterministic.
2. Keep neutralization and residualization logic explicit.
3. Keep capacity and transaction-cost helpers explicit.
4. Keep ensemble and diagnostics helpers explicit.

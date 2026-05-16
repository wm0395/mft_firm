# Hypothesis Registry

The hypothesis registry turns hypotheses from "code that happens to run" into governed research objects.

## Lifecycle

Supported statuses:

- `draft`: defined but not trusted
- `testing`: allowed in research runs, not production trade generation
- `active`: allowed in batch and trade-idea generation
- `deprecated`: visible, not evaluated by default
- `archived`: read-only historical record

Allowed transitions:

- `draft -> testing`
- `testing -> active`
- `active -> deprecated`
- `deprecated -> archived`

Use `--force` only when you explicitly want to override the safe path.

## CLI

List registered hypotheses:

```bash
python project/main.py list-hypotheses
```

Inspect one hypothesis:

```bash
python project/main.py show-hypothesis hypothesis:rsi_mean_reversion
```

Validate the registered definition:

```bash
python project/main.py validate-hypothesis hypothesis:rsi_mean_reversion
```

Promote a hypothesis through the lifecycle:

```bash
python project/main.py promote-hypothesis hypothesis:rsi_mean_reversion --to active
```

Research runs can also opt into broader evaluation with:

```bash
python project/main.py run-research-batch --include-testing --include-draft
python project/main.py run-strategy-research \
  --dataset-snapshot-id dataset_snapshot:us-largecap-daily-v1 \
  --hypothesis-id hypothesis:rsi_mean_reversion \
  --asset-symbol AAPL \
  --start-date 2024-01-01 \
  --end-date 2026-05-15 \
  --include-testing
```

## Why this matters

- `list-hypotheses` gives a fast inventory of governed research objects.
- `show-hypothesis` exposes the full definition, required signals, and status.
- `validate-hypothesis` checks signal registration and definition completeness.
- `promote-hypothesis` makes lifecycle changes explicit and auditable.
- `run-batch` only evaluates `active` hypotheses by default, which keeps draft or testing work out of production flows.

## Persistence

The code-defined catalog is persisted into:

- `hypotheses`
- `hypothesis_signal_map`
- `signal_registry`

The persistence path is idempotent, so seeding the catalog repeatedly does not create duplicates.

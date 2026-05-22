# Data Sources

This directory is the review surface for external market and macro sources.
It is a control document set, not an implementation contract.

Rules:

- `source_registry.yaml` is the source-of-truth index.
- `license_status` stays `unknown` until verified.
- `adapter_status` never implies production readiness.
- `data_quality_status` only advances after reproducible checks exist.
- No source may be treated as canonical without a documented legal review,
  field map, and sample quality report.

Status legend:

- `license_status`: `unknown`, `approved`, `rejected`, or `restricted`
- `adapter_status`: `not_started`, `prototype`, `validated`, or `production`
- `data_quality_status`: `not_assessed`, `sampled`, `blocked`, or `validated`

Review order:

1. Confirm the official URL and access method.
2. Verify license or terms of service and document allowed use.
3. Map raw fields to the canonical data contract.
4. Define frequency, history depth, freshness, and archive limits.
5. Add adapter fixtures, tests, and a data-quality report.
6. Promote status only after reproducible validation.

Sources here are candidates for the research factory, not production claims.

Current verification posture is tracked in `source_verification.md`.
No source is treated as production-ready here.

# Data Source Onboarding Checklist

Use this checklist before opening or promoting any adapter work.

## Required checks

- [ ] Confirm `source_id` and owner role.
- [ ] Record the official `base_url`.
- [ ] Verify license or terms of service.
- [ ] Mark `license_status` as `unknown` if verification is incomplete.
- [ ] List the asset classes the source can support.
- [ ] Define the raw fields expected from the source.
- [ ] Define the canonical fields and mapping rules.
- [ ] Record frequency, history depth, and access method.
- [ ] Capture rate-limit or politeness notes.
- [ ] Add a fixture or sample payload.
- [ ] Add parser and validation tests.
- [ ] Produce a quality report that separates source gaps from asset gaps.
- [ ] Keep `adapter_status` below `validated` until tests pass.
- [ ] Do not mark any source `production` without explicit review.

## Promotion gate

- Source metadata is complete.
- Canonical mapping is documented.
- Negative cases are covered.
- Quality report exists.
- Legal caveats are visible.

If any item is missing, the source remains review-only.

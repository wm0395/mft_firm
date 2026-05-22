# Initial Expansion Plan

The first multi-asset expansion is intentionally narrow:

1. Build a deterministic Indian ETF transfer lane from exact-OHLCV research.
2. Build MCX continuous contract construction before any commodity alpha claims.
3. Build macro regime overlays only after RBI/FRED coverage is explicit.
4. Keep FX/global proxy lanes research-only and non-authoritative.
5. Keep every queue item tied to explicit source dependencies, transform
   families, validation plans, and done conditions.

Promotion gates remain stricter than the current Alpha101 exact-OHLCV lane:

- no production claims without ingestion and quality checks
- no source without a registry entry
- no asset class without a source priority order
- no roll-based lane without explicit contract metadata

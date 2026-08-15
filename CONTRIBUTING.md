# Contributing

The most valuable contribution is correcting a `needs_review` mapping.

1. Find the row in `crosswalks/axis1-land-classification.yaml`.
2. Check the regional law's consolidated text on BOE (each row carries its
   citation).
3. Open a PR that: fixes the mapping if wrong, sets `confidence: verified`,
   and adds the BOE URL you checked in `verified_against`.

Rules:
- Map by **legal effect**, never by label similarity.
- Never delete a regional term — if a law was repealed, mark the vintage;
  plans approved under it still resolve through it.
- One region per PR keeps review fast.

CI validates: every mapping targets one of the 7 canonical values, citations
are present, and the YAML parses. `python validate.py` runs the same checks
locally.

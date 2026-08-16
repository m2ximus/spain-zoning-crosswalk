# Contributing

The most valuable contribution is correcting a `needs_review` mapping.

1. Find the row in `spain_zoning_crosswalk/crosswalks/axis1-land-classification.yaml`.
2. Check the regional law's consolidated text on BOE (each row carries its
   citation).
3. Open a PR that: fixes the mapping if wrong, sets `confidence: verified`,
   adds the BOE URL you checked in `verified_against`, and sets the region's
   `verified_at_version` to the version the PR releases.
4. Run `python validate.py --write` to regenerate the CSV, and commit it.

Rules:
- Map by **legal effect**, never by label similarity.
- Never delete a regional term — if a law was repealed, mark the vintage;
  plans approved under it still resolve through it.
- **Edit the YAML, never the CSV.** The CSV is generated from the YAML and CI
  fails if the committed file differs from what the YAML renders. A hand edit
  there is a change nobody reviews against the law.
- Use the law's own words for `local`. If a regional law titles the category
  *suelo no urbanizable especial*, that is the term — not the phrasing a
  neighbouring region uses for the same idea. A crosswalk whose job is
  translating local vocabulary cannot carry vocabulary the locality does not
  use, and a value read from that region's own service will not match it. If
  you are correcting a term rather than a mapping, keep the old string in
  `previous_local` so a consumer matching it can see why it stopped.
- One region per PR keeps review fast.

CI validates: every mapping targets one of the 7 canonical values, citations
are present, the YAML parses, the two version numbers agree, and the CSV is
exactly what the YAML generates. `python validate.py` runs the same checks
locally; `python -m pytest tests -q` covers the generator itself.

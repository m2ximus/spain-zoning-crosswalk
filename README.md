# spain-zoning-crosswalk

A harmonised crosswalk of Spanish regional zoning vocabularies to a canonical
7-class model, aligned with INSPIRE Planned Land Use / HILUCS.

Spain has 17 regional planning laws, each with its own land-classification
vocabulary. The INSPIRE standard that should unify them has been legally
required since Ley 14/2010 (LISIGE) and is implemented almost nowhere. This
repository is the missing mapping: every regional term, mapped by **legal
effect** (never by label) to seven canonical values:

    URBAN_CONSOLIDATED · URBAN_UNCONSOLIDATED ·
    DEVELOPABLE_SECTORED · DEVELOPABLE_UNSECTORED ·
    RURAL_SETTLEMENT · RURAL_ORDINARY · RURAL_PROTECTED

`RURAL_SETTLEMENT` exists because ten regions define a rural-nucleus figure
under ~ten different names, and a three-bucket model silently destroys it.

## Status

110 mappings across 17 regions + Ceuta/Melilla. Confidence per row:
`verified` (checked against the BOE consolidated text), `high`, or
`needs_review`. **11 regions currently need review — corrections welcome**,
especially from regional GIS and urbanism staff. See CONTRIBUTING.md.

## Versioning

Semver tags. Consumers should pin a tag and record it (`crosswalk_version`)
next to any data resolved through it. Mappings resolve against the law in
force **when the plan was approved**, never against today's law.

The version lives in two places — `version` in `pyproject.toml` and
`meta.version` in the crosswalk YAML — and `validate.py` asserts they are
equal, so CI goes red on drift. **Bump both in the same commit or validation
fails.** A consumer recording `crosswalk_version` cannot tell which of the two
it received, so they are never allowed to disagree.

Release history:

| Tag | Notes |
|-----|-------|
| `v0.1.1` | Data only — not pip-installable (no packaging metadata). |
| `v0.1.2` | First installable release; `meta.version` was still stale in-file. |
| `v0.1.3` | First self-consistent release; version sync enforced by CI. |
| `v0.1.4` | Adds OQ-5: the ordinario/protegido distinction is not carried as a feature layer by the Andalusian regional services surveyed 2026-08-16, with the services listed by URL. |

## Licence

CC-BY-4.0. Maintained by Casas Unitas. Attribution: "spain-zoning-crosswalk,
CC-BY-4.0".

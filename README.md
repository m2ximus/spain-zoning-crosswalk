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

162 mappings across 17 regions + Ceuta/Melilla. Confidence per row:
`verified` (the operative articles read directly, with the text, the date and
the limits of the reading recorded in the region's `verified_note`), `high`, or
`needs_review`. **11 regions are verified as of v0.2.0; 6 need review —
corrections welcome**, especially from regional GIS and urbanism staff. See
CONTRIBUTING.md.

Four attributes were added at v0.2.0 because the flat `{local, canonical}` pair
could not carry them without guessing:

| Key | Answers |
|---|---|
| `protection_basis` | **why** a `RURAL_PROTECTED` row is protected — one or more of `environmental`, `economic`, `infrastructure`, `coastal`, `interest`, `plan`, `sectoral`, `risk`, `none`. Eight regions put natural or technological risk in eight different places, so it is a property of the row, not of the canonical value. |
| `settlement_position` | **where** a `RURAL_SETTLEMENT` sits: `own_class`, `within_rural`, `none`. |
| `rural_settlement` | that an `URBAN_*` row nonetheless carries a settlement régimen (Murcia art. 81.4, Cantabria after 2024-01-01). **A resolver must branch on this before answering "what may I build here"** — the class is urban, the permissions are not. |
| `valid_from` / `valid_to` | **when** the row was true. Vocabulary changes on statutory dates and a plan drafted earlier carries the older word. |

`protection_basis` records what a STATUTE says about a category. It is never
evidence about a parcel, and it may not be used to infer protection from land
use: extractive land is protected in Canarias (SRPM) and common rural in the
Comunitat Valenciana (ZRC-EX). Same fact, opposite answers.

## Versioning

Semver tags. Consumers should pin a tag and record it (`crosswalk_version`)
next to any data resolved through it. Mappings resolve against the law in
force **when the plan was approved**, never against today's law.

The version lives in two places — `version` in `pyproject.toml` and
`meta.version` in the crosswalk YAML — and `validate.py` asserts they are
equal, so CI goes red on drift. **Bump both in the same commit or validation
fails.** A consumer recording the crosswalk version cannot tell which of the
two it received, so they are never allowed to disagree.

### Two different versions, and they are not the same number

| Where | Means |
|---|---|
| `meta.version` in the YAML, `version` in `pyproject.toml`, the git tag | **the version of this file.** One number, always in step. This is what a consumer pins. |
| `verified_at_version` per region (a column in the CSV, a key per region in the YAML) | **the version at which THAT REGION was last established against the law.** |

They differ on purpose and usually do. At v0.2.0 ten regions carry
`verified_at_version: 0.2.0` — the ten read article by article for this release
— La Rioja still carries `0.1.5`, because it was read then and nothing was
re-read now, and the remaining six still say `0.1.1-draft`. That last group is
the honest answer: the file moved, those rows did not. Bumping them along with
the file would erase the only signal that says which rows have been checked
recently and which are inherited.

The per-row column was called `crosswalk_version` through v0.1.4, which read
naturally as either meaning. It is now `verified_at_version`. If you consumed
that column, the values are unchanged — only the name is.

### The CSV is generated

`axis1-land-classification.csv` is rendered from the YAML by `validate.py`, and
CI fails if the committed CSV differs from what the YAML generates. Do not edit
it by hand — edit the YAML and run `python validate.py --write`. The CSV is
lossy on purpose: notes, `previous_local` and the schema pins live only in the
YAML.

Release history:

| Tag | Notes |
|-----|-------|
| `v0.1.1` | Data only — not pip-installable (no packaging metadata). |
| `v0.1.2` | First installable release; `meta.version` was still stale in-file. |
| `v0.1.3` | First self-consistent release; version sync enforced by CI. |
| `v0.1.5` | La Rioja verified against the consolidated Ley 5/2006 (arts. 38, 42, 45, 46, 55, 57); `suelo no urbanizable de especial protección` corrected to the law's own `suelo no urbanizable especial`. The CSV becomes a generated artefact and the per-row stamp is renamed `verified_at_version`. |
| `v0.2.0` | Ten regions verified against BOE consolidated texts and, for the bilingual communities, the authentic regional gazette: Catalunya, Galicia, Cantabria, Extremadura, Canarias, Aragón, Asturias, Comunitat Valenciana, Illes Balears, Región de Murcia. 110 → 162 mappings. Adds `protection_basis`, `settlement_position`, `rural_settlement`, `valid_from`/`valid_to`, `local_code` and `previous_local`; the first five reach the CSV. Six vocabulary leaks corrected with the replaced string preserved, two rows removed as figures their statute does not contain, and Andalucía downgraded to `needs_review` because it claimed `verified` without recording what was read. |
| `v0.1.4` | Adds OQ-5: the ordinario/protegido distinction is not carried as a feature layer by the Andalusian regional services surveyed 2026-08-16, with the services listed by URL. |

## Licence

CC-BY-4.0. Maintained by Casas Unitas. Attribution: "spain-zoning-crosswalk,
CC-BY-4.0".

#!/usr/bin/env python3
"""Validate the crosswalk against its real structure. CI fails on any error.

Structure: top-level `regions` is a list; each region carries law, confidence
and a `mappings` list of {local, canonical, ...}. Law citation lives at region
level (one law per region), confidence likewise.
"""
import sys
import tomllib
from pathlib import Path

from spain_zoning_crosswalk import csvgen

try:
    import yaml
except ImportError:
    sys.exit("pip install pyyaml")

HERE = Path(__file__).parent

# The data ships inside the package dir so it can be installed as package data.
# Resolved relative to this file so validation needs no install -- CI runs it
# with pyyaml alone.
DATA = HERE / "spain_zoning_crosswalk" / "crosswalks" / "axis1-land-classification.yaml"
CSV = HERE / "spain_zoning_crosswalk" / "crosswalks" / "axis1-land-classification.csv"
PYPROJECT = HERE / "pyproject.toml"
WRITE = "--write" in sys.argv

CANON = {"URBAN_CONSOLIDATED","URBAN_UNCONSOLIDATED","DEVELOPABLE_SECTORED",
         "DEVELOPABLE_UNSECTORED","RURAL_SETTLEMENT","RURAL_ORDINARY","RURAL_PROTECTED"}
CONF = {"verified","high","needs_review"}

doc = yaml.safe_load(DATA.read_text(encoding="utf-8"))
errs, total = [], 0

# --- Version sync -----------------------------------------------------------
# The distribution version and the version recorded INSIDE the data must agree.
# A consumer that records crosswalk_version has no way to tell which one it got,
# so drift here silently mislabels the provenance of resolved answers. Bump both
# in the same commit or CI goes red.
dist_version = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]["version"]
meta_version = doc.get("meta", {}).get("version")
if meta_version != dist_version:
    errs.append(
        f"version drift: pyproject.toml has {dist_version!r} but "
        f"{DATA.name} meta.version is {meta_version!r} — bump both together"
    )

regions = doc.get("regions", [])
if len(regions) < 17:
    errs.append(f"expected >=17 regions, found {len(regions)}")

seen_canon = set()
for r in regions:
    name = r.get("region", "?")
    if r.get("confidence") not in CONF:
        errs.append(f"{name}: region confidence {r.get('confidence')!r} invalid")
    if not r.get("law"):
        errs.append(f"{name}: missing law citation")
    mm = r.get("mappings", [])
    if not mm:
        errs.append(f"{name}: no mappings")
    for m in mm:
        total += 1
        c = m.get("canonical")
        if c not in CANON:
            errs.append(f"{name}/{m.get('local','?')}: canonical {c!r} not in canonical set")
        seen_canon.add(c)
        if not m.get("local"):
            errs.append(f"{name}: mapping missing local term")

# --- The CSV is a build artefact -------------------------------------------
# It was hand-maintained until 0.1.5 and nothing checked it, which made it a
# second source of truth for the same 110 mappings — the kind that stays wrong
# quietly, because the file that is read by consumers is not the file that is
# reviewed. It is now rendered from the YAML. `--write` regenerates it; without
# it, a difference is an error, so a hand edit fails the build instead of
# shipping. The first run of this check found one: a comma dropped from an
# article citation to avoid having to quote the field.
rendered = csvgen.render(doc)
if WRITE:
    CSV.write_text(rendered, encoding="utf-8")
    print(f"wrote {CSV.name}")
elif not CSV.exists():
    errs.append(f"{CSV.name} is missing — regenerate it with `python validate.py --write`")
elif CSV.read_text(encoding="utf-8") != rendered:
    errs.append(
        f"{CSV.name} is not what {DATA.name} generates. The CSV is output, not "
        "a place to edit: regenerate it with `python validate.py --write` and "
        "commit the result. If the difference is one you meant, you meant it in "
        "the YAML."
    )

# Every region declares the version at which it was last established. The column
# used to be called crosswalk_version, which read as the version of the FILE and
# stamped rows nobody had re-checked with a version that implied somebody had.
for r in regions:
    if not r.get("verified_at_version"):
        errs.append(f"{r.get('region','?')}: no verified_at_version")

missing = CANON - seen_canon
if missing:
    errs.append(f"canonical values never used: {sorted(missing)}")

for e in errs:
    print("ERROR:", e)
print(f"{len(regions)} regions, {total} mappings, {len(errs)} errors")
sys.exit(1 if errs else 0)

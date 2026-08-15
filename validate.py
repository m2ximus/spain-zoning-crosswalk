#!/usr/bin/env python3
"""Validate the crosswalk against its real structure. CI fails on any error.

Structure: top-level `regions` is a list; each region carries law, confidence
and a `mappings` list of {local, canonical, ...}. Law citation lives at region
level (one law per region), confidence likewise.
"""
import sys
import tomllib
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("pip install pyyaml")

HERE = Path(__file__).parent

# The data ships inside the package dir so it can be installed as package data.
# Resolved relative to this file so validation needs no install -- CI runs it
# with pyyaml alone.
DATA = HERE / "spain_zoning_crosswalk" / "crosswalks" / "axis1-land-classification.yaml"
PYPROJECT = HERE / "pyproject.toml"

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

missing = CANON - seen_canon
if missing:
    errs.append(f"canonical values never used: {sorted(missing)}")

for e in errs:
    print("ERROR:", e)
print(f"{len(regions)} regions, {total} mappings, {len(errs)} errors")
sys.exit(1 if errs else 0)

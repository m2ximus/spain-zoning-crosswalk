#!/usr/bin/env python3
"""Validate the crosswalk against its real structure. CI fails on any error.

Structure: top-level `regions` is a list; each region carries law, confidence
and a `mappings` list of {local, canonical, ...}. Law citation lives at region
level (one law per region), confidence likewise.
"""
import sys
try:
    import yaml
except ImportError:
    sys.exit("pip install pyyaml")

CANON = {"URBAN_CONSOLIDATED","URBAN_UNCONSOLIDATED","DEVELOPABLE_SECTORED",
         "DEVELOPABLE_UNSECTORED","RURAL_SETTLEMENT","RURAL_ORDINARY","RURAL_PROTECTED"}
CONF = {"verified","high","needs_review"}

doc = yaml.safe_load(open("crosswalks/axis1-land-classification.yaml", encoding="utf-8"))
errs, total = [], 0
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

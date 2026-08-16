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

# Added at 0.2.0, and duplicated deliberately from tests/test_verified_region_
# schema.py. The tests are the discipline; this file is the gate a CONSUMER runs,
# with pyyaml alone and no pytest, and a vocabulary that only pytest enforces is
# not enforced for them. `risk` is here because the reading forced it; there is no
# `within_urban` because the settlement-inside-urban case maps to URBAN_* with the
# `rural_settlement` flag instead. Both decisions are argued in the YAML.
BASIS = {"environmental","economic","infrastructure","coastal",
         "interest","plan","sectoral","risk","none"}
POSITION = {"own_class","within_rural","none"}

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

        where = f"{name}/{m.get('local','?')}"
        pb = m.get("protection_basis")
        if pb is not None:
            vals = pb if isinstance(pb, list) else [pb]
            bad = sorted(set(vals) - BASIS)
            if bad:
                errs.append(f"{where}: protection_basis {bad} not in vocabulary")
            if len(vals) > 1 and "none" in vals:
                errs.append(f"{where}: `none` cannot be one basis among several")
            # A protected-land reason on buildable land is a sectoral overlay
            # leaking onto the classification axis, which is the one thing this
            # crosswalk exists to prevent.
            if str(c).startswith(("URBAN_", "DEVELOPABLE_")):
                errs.append(f"{where}: protection_basis on {c}")
        elif c == "RURAL_PROTECTED" and r.get("confidence") == "verified":
            errs.append(f"{where}: RURAL_PROTECTED in a verified region with no protection_basis")

        sp = m.get("settlement_position")
        if sp is not None:
            if sp not in POSITION:
                errs.append(f"{where}: settlement_position {sp!r} not in vocabulary")
            if c != "RURAL_SETTLEMENT":
                errs.append(f"{where}: settlement_position on {c}")

        rs = m.get("rural_settlement")
        if rs is not None:
            if not isinstance(rs, bool):
                errs.append(f"{where}: rural_settlement must be true or false")
            elif rs and not str(c).startswith("URBAN_"):
                # The flag exists for the figures a statute puts INSIDE urban
                # land (Murcia art. 81.4, Cantabria after 2024). Anywhere else it
                # either duplicates the canonical value or contradicts it.
                errs.append(f"{where}: rural_settlement is true on {c}")

        if m.get("valid_to") and not m.get("valid_from"):
            errs.append(f"{where}: valid_to with no valid_from")
        if m.get("valid_from") and m.get("valid_to") and m["valid_from"] >= m["valid_to"]:
            errs.append(f"{where}: valid_from is not before valid_to")

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

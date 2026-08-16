"""The CSV is generated from the YAML, or it is a second source of truth.

It was hand-maintained until v0.1.5, and validate.py never looked at it. Two
files describing the same 110 mappings, one of them unchecked, is a drift the
next contributor finds by shipping it: the YAML says `suelo no urbanizable
especial` and the CSV still says whatever the last person typed, and a consumer
reading the CSV gets an answer nobody verified.

These tests fix the direction of truth. The YAML is the source; the CSV is
output. Nothing here checks that the CSV is *correct* — that is what reading the
law is for — only that it cannot say something the YAML does not.
"""
import csv
import io
from pathlib import Path

import pytest
import yaml

from spain_zoning_crosswalk import csvgen

ROOT = Path(__file__).resolve().parent.parent
YAML = ROOT / "spain_zoning_crosswalk" / "crosswalks" / "axis1-land-classification.yaml"
CSV = ROOT / "spain_zoning_crosswalk" / "crosswalks" / "axis1-land-classification.csv"


@pytest.fixture(scope="module")
def doc():
    return yaml.safe_load(YAML.read_text(encoding="utf-8"))


def test_the_committed_csv_is_exactly_what_the_yaml_generates(doc):
    # The whole point. If this fails, either someone edited the CSV by hand or
    # the YAML moved and the CSV was not regenerated. Both are the same defect
    # seen from two sides, and both are fixed the same way: regenerate.
    assert CSV.read_text(encoding="utf-8") == csvgen.render(doc)


def test_a_hand_edit_to_the_csv_is_detected(doc, tmp_path):
    tampered = CSV.read_text(encoding="utf-8").replace(
        "suelo no urbanizable especial", "suelo no urbanizable de especial protección")
    assert tampered != CSV.read_text(encoding="utf-8"), "the tamper did nothing"
    assert tampered != csvgen.render(doc)


def test_every_mapping_in_the_yaml_reaches_the_csv(doc):
    rows = list(csv.DictReader(io.StringIO(csvgen.render(doc))))
    assert len(rows) == sum(len(r["mappings"]) for r in doc["regions"])
    pairs = {(r["region"], m["local"]) for r in doc["regions"] for m in r["mappings"]}
    assert {(r["region"], r["local_term"]) for r in rows} == pairs


def test_the_row_stamp_is_named_verified_at_version(doc):
    # `crosswalk_version` meant two different things depending on where you read
    # it: the version of the FILE, and the version at which a ROW was last
    # established. Ten regions still stamped 0.1.1-draft in a file at 0.1.5 is
    # honest under the second reading and a lie under the first, and a column
    # name that admits both readings will be read the wrong way eventually.
    header = csvgen.render(doc).splitlines()[0].split(",")
    assert "verified_at_version" in header
    assert "crosswalk_version" not in header


def test_every_region_declares_the_version_it_was_last_established_at(doc):
    missing = [r["region"] for r in doc["regions"] if not r.get("verified_at_version")]
    assert missing == [], f"no row stamp for: {missing}"


def test_a_regions_stamp_never_runs_ahead_of_the_file(doc):
    # A row cannot have been established at a version that does not exist yet.
    # Stamps BEHIND meta.version are the normal case and are left alone: they
    # are the ten regions nobody has verified since 0.1.1-draft, and quietly
    # bumping them to the current version is exactly the lie this column exists
    # to prevent.
    def key(v):
        return tuple(int(p) for p in v.split("-")[0].split("."))

    here = key(doc["meta"]["version"])
    ahead = [r["region"] for r in doc["regions"] if key(r["verified_at_version"]) > here]
    assert ahead == [], f"stamped at an unreleased version: {ahead}"


def test_the_stamp_records_when_the_region_was_verified(doc):
    # REPLACES test_the_stamp_matches_the_confidence_it_claims, which required
    # every verified region to be stamped at meta.version. That was true while
    # exactly one region had been verified and becomes false the moment a second
    # release verifies others: it would force La Rioja, read at 0.1.5, to claim
    # it was read at 0.2.0. The honest invariant is weaker and checkable — a
    # verified region's stamp is the version at which somebody actually read it,
    # so it is a real released version, never the draft placeholder, and never
    # ahead of meta.version (which the test above already covers for all rows).
    for r in doc["regions"]:
        if r.get("confidence") != "verified":
            continue
        stamp = r.get("verified_at_version")
        assert stamp, f"{r['region']}: verified with no verified_at_version"
        assert "draft" not in stamp, (
            f"{r['region']} claims verified but is stamped {stamp} — a draft "
            "stamp means nobody recorded a reading")


def test_this_releases_regions_carry_this_releases_version(doc):
    # The ten regions read for 0.2.0 must say so. Without this, the previous
    # test's weakening would let a region be upgraded to `verified` while keeping
    # an older stamp, which reads as "verified long ago" and is unfalsifiable.
    this_release = {
        "Catalunya", "Galicia", "Cantabria", "Extremadura", "Canarias",
        "Aragón", "Principado de Asturias", "Comunitat Valenciana",
        "Illes Balears", "Región de Murcia",
    }
    by_name = {r["region"]: r for r in doc["regions"]}
    for name in this_release:
        r = by_name[name]
        assert r["confidence"] == "verified", f"{name}: not verified"
        assert r["verified_at_version"] == "0.2.0", (
            f"{name} was verified in this release but is stamped "
            f"{r['verified_at_version']}")

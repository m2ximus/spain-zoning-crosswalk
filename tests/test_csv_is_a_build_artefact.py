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


def test_the_stamp_matches_the_confidence_it_claims(doc):
    # A region at `verified` carries verified_against and verified_on. The stamp
    # is the third part of the same claim; a `verified` region still stamped at
    # the version before anybody looked means one of the three was updated alone.
    for r in doc["regions"]:
        if r.get("confidence") == "verified" and r.get("verified_on"):
            assert r["verified_at_version"] == doc["meta"]["version"], (
                f"{r['region']} claims verified_on {r['verified_on']} but is "
                f"stamped {r['verified_at_version']}")

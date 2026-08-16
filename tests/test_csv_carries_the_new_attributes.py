"""The CSV is lossy by design, but not about anything that changes an answer.

v0.2.0 added four things a flat consumer cannot reconstruct from the columns it
already had:

  protection_basis     WHY a row is protected. A consumer filtering "protected
                       because of flood risk" has no other source for it.
  rural_settlement     that an URBAN_* row carries a settlement régimen
                       (Murcia art. 81.4, Cantabria after 2024). Without it the
                       CSV says "urban land" and the reader builds a house.
  settlement_position  where a RURAL_SETTLEMENT sits.
  valid_from/valid_to  WHEN the row was true. This is the one that fails
                       silently: without it a 2010 plan matches today's row and
                       the CSV cannot say the vocabulary changed underneath it.
  local_code           Valencia's statutory zone codes (ANEXO IV §I.1) — the only
                       machine-matchable keys in the file, and useless if the CSV
                       drops them.

`previous_local` and the notes stay out, per the module docstring: they explain
the file's history rather than answer a question about a parcel.
"""
from pathlib import Path

import pytest
import yaml

from spain_zoning_crosswalk import csvgen

ROOT = Path(__file__).resolve().parent.parent
YAML = ROOT / "spain_zoning_crosswalk" / "crosswalks" / "axis1-land-classification.yaml"

NEW = ["local_code", "protection_basis", "rural_settlement",
       "settlement_position", "valid_from", "valid_to"]


@pytest.fixture(scope="module")
def doc():
    return yaml.safe_load(YAML.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def by_key(doc):
    return {(r["region"], r["local_term"]): r for r in csvgen.rows(doc)}


def test_the_new_columns_exist():
    for col in NEW:
        assert col in csvgen.COLUMNS, f"CSV drops {col}"


def test_a_multi_valued_basis_survives_the_flattening(by_key):
    # Murcia art. 83.1.a) carries six grounds. A flat cell has to join them, and
    # the separator must not be the comma the CSV itself uses.
    row = by_key[("Región de Murcia", "suelo no urbanizable de protección específica")]
    assert row["protection_basis"] == (
        "environmental;interest;risk;coastal;infrastructure;sectoral")


def test_a_single_valued_basis_is_not_wrapped_in_list_syntax(by_key):
    row = by_key[("Comunitat Valenciana", "ZRP-RI")]
    assert row["protection_basis"] == "risk"


def test_an_unprotected_row_says_nothing_rather_than_none(by_key):
    row = by_key[("Región de Murcia", "suelo urbano consolidado")]
    assert row["protection_basis"] == ""


def test_the_settlement_flag_reaches_the_csv(by_key):
    # The row this whole column exists for: URBAN by class, settlement by effect.
    row = by_key[("Región de Murcia", "suelo urbano de núcleo rural")]
    assert row["canonical"] == "URBAN_CONSOLIDATED"
    assert row["rural_settlement"] is True


def test_a_vintage_reaches_the_csv(by_key):
    # Balears: RURAL_SETTLEMENT under LSRIB art. 8 ended when DL 2/2012 repealed
    # it. A CSV that drops valid_to answers a 2005 plan with a 2026 row.
    row = by_key[("Illes Balears", "nucli rural")]
    assert str(row["valid_to"]) == "2012-02-18"


def test_valencias_zone_codes_reach_the_csv(by_key):
    row = by_key[("Comunitat Valenciana", "ZRC-EX")]
    assert row["local_code"] == "ZRC-EX"

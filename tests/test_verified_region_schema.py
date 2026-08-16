"""What a `verified` region must carry, and what the new attributes may say.

v0.1.5 verified one region (La Rioja) by hand and proved the shape works. This
release verifies ten more against BOE consolidated texts and regional gazettes,
and in doing so hit three things the flat {local, canonical} pair cannot express
without guessing:

  1. WHY a RURAL_PROTECTED row is protected. Eight regions put natural or
     technological RISK in eight different places — the protected category
     (Cantabria, Aragón, Murcia), the ordinary one (Galicia), a category of its
     own (Extremadura `restringido`), bundled with other grounds (Asturias),
     a coded zone (Valencia ZRP-RI), and the CLASS itself with no category at
     all (Illes Balears, LSRIB art. 4.2.c). A consumer asking "is this parcel
     protected because of flood risk" cannot answer from the canonical value,
     and inferring it from the label is the guess this file exists to prevent.

  2. WHERE a rural settlement sits. `RURAL_SETTLEMENT` is one canonical value
     covering figures that are a class of their own, a category inside rural
     land, and a category inside URBAN land (Murcia art. 81.4, Cantabria after
     2024). The legal effect is the same — a recognised settlement where
     residential building is specifically permitted — but the class the plan
     writes on the parcel is not, and ingest matches on the class.

  3. WHEN a row was true. Vocabulary changes on statutory dates, and a plan
     drafted before that date carries the old word. Rows that differ only by
     vintage need `valid_from` / `valid_to` or they silently overwrite history.

These tests pin the vocabulary of those three attributes and the discipline that
`verified` implies. They do not check that any mapping is CORRECT — that is what
reading the articles is for, and it is recorded in each region's verified_note.
"""
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
YAML = ROOT / "spain_zoning_crosswalk" / "crosswalks" / "axis1-land-classification.yaml"

# Deliberately the brief's eight values plus `risk`. `risk` was forced by the
# reading: it is named in the operative text of eight of the eleven verified
# regions and lands in a different slot in each, so it is a property of the row
# and not of the canonical value. Nothing else was added — `landscape`,
# `heritage` and the rest of the statutory grounds are folded into
# `environmental` / `interest` and spelled out verbatim in each row's note,
# because splitting them further multiplies the vocabulary faster than any
# consumer can use it. See OPEN QUESTIONS in the YAML.
PROTECTION_BASIS = {
    "environmental", "economic", "infrastructure", "coastal",
    "interest", "plan", "sectoral", "risk", "none",
}

# `within_urban` was in the brief's proposal and is NOT here. The reading killed
# it. Murcia art. 81.4 and Cantabria after 2024 put their settlement figure
# inside the URBAN class, and the owner's rule for those is that the row maps to
# the URBAN_* family — the class the plan writes is the class ingest matches on —
# and carries a `rural_settlement: true` flag for the effect. So no row can
# legitimately be RURAL_SETTLEMENT *and* sit within urban land: the two halves of
# `within_urban` contradict each other. Retiring the value is what stops the
# contradiction being expressible.
SETTLEMENT_POSITION = {"own_class", "within_rural", "none"}


@pytest.fixture(scope="module")
def doc():
    return yaml.safe_load(YAML.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def verified(doc):
    return [r for r in doc["regions"] if r.get("confidence") == "verified"]


def mappings(regions):
    for r in regions:
        for m in r.get("mappings", []):
            yield r["region"], m


def test_the_ten_regions_of_this_release_are_verified(verified):
    # La Rioja was verified at 0.1.5. These ten were read article by article
    # against BOE consolidated texts and, for the bilingual communities, the
    # authentic regional gazette. Murcia is included: the brief could not reach
    # it, but BOE-A-2015-4790 (not ...-4795, which is a different disposition)
    # was fetched and its operative articles read.
    expected = {
        "La Rioja", "Catalunya", "Galicia", "Cantabria", "Extremadura",
        "Canarias", "Aragón", "Principado de Asturias", "Comunitat Valenciana",
        "Illes Balears", "Región de Murcia",
    }
    assert {r["region"] for r in verified} >= expected


def test_verified_means_somebody_names_what_they_read(verified):
    # `verified` is a claim about an act, not a confidence level. The claim is
    # only checkable if the row says which text, on what date, and with what
    # caveats — La Rioja's note, for instance, records that the archived bytes
    # do not establish how many modifications stand behind the date.
    for r in verified:
        for field in ("verified_against", "verified_on", "verified_note"):
            assert r.get(field), f"{r['region']}: verified but no {field}"


def test_protection_basis_uses_the_agreed_vocabulary(doc):
    for region, m in mappings(doc["regions"]):
        pb = m.get("protection_basis")
        if pb is None:
            continue
        values = pb if isinstance(pb, list) else [pb]
        assert values, f"{region}/{m['local']}: empty protection_basis"
        bad = set(values) - PROTECTION_BASIS
        assert not bad, f"{region}/{m['local']}: unknown protection_basis {sorted(bad)}"
        assert len(values) == len(set(values)), (
            f"{region}/{m['local']}: repeated protection_basis value")
        if len(values) > 1:
            assert "none" not in values, (
                f"{region}/{m['local']}: `none` cannot be one basis among several")


def test_every_protected_row_in_a_verified_region_says_why(verified):
    # The point of the attribute. A verified region has had its articles read,
    # so the grounds are known; leaving the field off would mean the reading
    # happened and the result was not written down.
    for region, m in mappings(verified):
        if m["canonical"] == "RURAL_PROTECTED":
            assert m.get("protection_basis"), (
                f"{region}/{m['local']}: RURAL_PROTECTED with no protection_basis")


def test_protection_basis_is_not_claimed_for_buildable_land(doc):
    # URBAN_* and DEVELOPABLE_* rows are not protected land. A basis there would
    # be a sectoral overlay leaking onto the classification axis, which is the
    # one thing this crosswalk must never do.
    for region, m in mappings(doc["regions"]):
        if m["canonical"].startswith(("URBAN_", "DEVELOPABLE_")):
            assert not m.get("protection_basis"), (
                f"{region}/{m['local']}: protection_basis on {m['canonical']}")


def test_settlement_position_uses_the_agreed_vocabulary(doc):
    for region, m in mappings(doc["regions"]):
        sp = m.get("settlement_position")
        if sp is None:
            continue
        assert sp in SETTLEMENT_POSITION, (
            f"{region}/{m['local']}: unknown settlement_position {sp!r}")


def test_every_settlement_row_in_a_verified_region_says_where_it_sits(verified):
    for region, m in mappings(verified):
        if m["canonical"] == "RURAL_SETTLEMENT":
            sp = m.get("settlement_position")
            assert sp, f"{region}/{m['local']}: RURAL_SETTLEMENT with no settlement_position"
            assert sp != "none", (
                f"{region}/{m['local']}: a settlement that sits nowhere is not a settlement")


def test_settlement_position_is_only_claimed_for_settlements(doc):
    for region, m in mappings(doc["regions"]):
        if m.get("settlement_position") and m["canonical"] != "RURAL_SETTLEMENT":
            pytest.fail(f"{region}/{m['local']}: settlement_position on {m['canonical']}")


def test_a_settlement_inside_urban_land_is_urban_land_with_a_flag(doc):
    # The owner's rule, as a test. Murcia's `suelo urbano de núcleo rural` is a
    # category of URBAN land (arts. 81.4, 88, 90); mapping it RURAL_SETTLEMENT
    # would import Galicia's concept into Murcia. Cantabria after 2024-01-01 is
    # the same shape. The flag is where the settlement effect lives, so it may
    # only appear on a row that is not already a settlement by canonical value.
    for region, m in mappings(doc["regions"]):
        if "rural_settlement" not in m:
            continue
        assert isinstance(m["rural_settlement"], bool), (
            f"{region}/{m['local']}: rural_settlement must be a boolean")
        assert m["canonical"] != "RURAL_SETTLEMENT", (
            f"{region}/{m['local']}: rural_settlement on a RURAL_SETTLEMENT row "
            "says nothing — the canonical value already says it")
        if m["rural_settlement"]:
            assert m["canonical"].startswith("URBAN_"), (
                f"{region}/{m['local']}: rural_settlement is true on "
                f"{m['canonical']} — the flag exists for settlements the statute "
                "puts inside URBAN land")


def test_a_flagged_settlement_says_what_régimen_it_carries(verified):
    # A row whose class and effect point different ways is exactly the row a
    # consumer will get wrong, so it does not get to be terse. The note is where
    # art. 90 (Murcia) or art. 111.1 (Cantabria) is quoted.
    for region, m in mappings(verified):
        if m.get("rural_settlement") is True:
            assert m.get("note"), (
                f"{region}/{m['local']}: flagged as a settlement inside urban "
                "land with no note saying what may actually be built")
            assert m.get("article"), (
                f"{region}/{m['local']}: flagged as a settlement with no article")


def test_a_vintage_row_says_when_it_was_true(doc):
    # valid_from / valid_to are dates the LAW fixes, not dates we looked. A row
    # with valid_to and no valid_from cannot be placed on a timeline.
    for region, m in mappings(doc["regions"]):
        if m.get("valid_to") is not None:
            assert m.get("valid_from"), (
                f"{region}/{m['local']}: valid_to with no valid_from")
        if m.get("valid_from") and m.get("valid_to"):
            assert m["valid_from"] < m["valid_to"], (
                f"{region}/{m['local']}: valid_from is not before valid_to")


def test_superseded_rows_are_kept_not_deleted(doc):
    # The vintage splits exist so that a plan drafted under the old vocabulary
    # still resolves. A region that gained a valid_from must therefore also
    # carry the row it replaced, or the split deleted history instead of
    # recording it.
    for r in doc["regions"]:
        closed = [m for m in r.get("mappings", []) if m.get("valid_to")]
        open_ = [m for m in r.get("mappings", []) if m.get("valid_from") and not m.get("valid_to")]
        if closed:
            assert open_, (
                f"{r['region']}: has superseded rows but no successor still open")


def test_a_corrected_string_keeps_the_one_it_replaced(doc):
    # previous_local is how a leak stays visible after it is fixed. It must
    # differ from the string that replaced it, or the correction is cosmetic.
    for region, m in mappings(doc["regions"]):
        if "previous_local" in m:
            assert m["previous_local"] != m["local"], (
                f"{region}/{m['local']}: previous_local repeats local")


def test_no_verified_region_carries_another_regions_vocabulary(verified):
    # The La Rioja lesson, as a test. Each entry is a string that a specific
    # region's operative text does NOT contain, found in that region's rows and
    # corrected in this release. Reintroducing one is a regression, and the
    # count of terms a law does not use is not something a reviewer can eyeball.
    # CORRECTED at v0.2.0. Three of these entries were wrong when first written:
    # they named strings that were never in the file verbatim, so the assertions
    # passed without checking anything, and one of them ("suelo no urbanizable
    # genérico") is a string Asturias legitimately kept. Each entry below was
    # taken from `git show main:` of the pre-release file, so every one is a
    # string that WAS there and is now gone. Correcting a wrong assertion is not
    # the same as loosening a check — the fixed version is strictly stronger,
    # because the old one could not fail.
    leaks = {
        "Catalunya": [
            "sòl no urbanitzable de protecció especial",
            "nucli rural / masia o casa rural inclosa en catàleg",
        ],
        "Extremadura": ["suelo rústico (común)"],
        "Principado de Asturias": ["núcleo rural (Catálogo del Principado)"],
        "Comunitat Valenciana": ["sòl urbà no consolidat", "nucli rural / núcleo rural"],
        "Illes Balears": ["sòl urbà no consolidat"],
        "Región de Murcia": ["suelo no urbanizable inadecuado / común"],
    }
    by_name = {r["region"]: r for r in verified}
    for region, banned in leaks.items():
        if region not in by_name:
            continue
        locals_ = {m["local"] for m in by_name[region]["mappings"]}
        for term in banned:
            assert term not in locals_, (
                f"{region}: `{term}` is back — the law does not use it")

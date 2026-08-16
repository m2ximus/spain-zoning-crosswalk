"""Render the crosswalk YAML as the flat CSV.

The CSV exists because a lot of consumers want one row per mapping and no YAML
parser. It is a VIEW of the YAML and never a second place to edit: `validate.py`
regenerates it and fails if the committed file differs, so a hand edit shows up
as a failing build rather than as a divergence nobody notices.

Anything the flat shape cannot carry — the per-mapping notes, the region notes,
`previous_local`, the schema pins — stays in the YAML on purpose. The CSV is
lossy by design; it is not a serialisation format.
"""
import csv
import io

#: `protection_basis` is a list in the YAML and a flat cell here, so it needs a
#: separator that is not the comma the CSV itself uses. Semicolon, no spaces.
BASIS_SEP = ";"

COLUMNS = [
    "region", "ine_ca_code", "law", "local_term", "local_term_es", "local_code",
    "canonical",
    "article", "legacy", "label_abolished", "flag",
    # Added at 0.2.0. Everything here answers a question about a PARCEL that the
    # other columns cannot: why a row is protected, that an URBAN_* row carries a
    # settlement régimen, where a settlement sits, and when the row was true.
    # `previous_local` and the notes stay in the YAML — they explain the file's
    # history, which is a different question.
    "protection_basis", "rural_settlement", "settlement_position",
    "valid_from", "valid_to",
    "confidence",
    # NOT `crosswalk_version`. That name was read two ways — the version of this
    # FILE and the version at which this ROW was last established — and the two
    # differ for every region nobody has re-checked since 0.1.1-draft. See
    # README.
    "verified_at_version",
]


def _basis(m):
    """Flatten protection_basis, which is a list, a bare string, or absent."""
    pb = m.get("protection_basis")
    if pb is None:
        return ""
    if isinstance(pb, str):
        return pb
    return BASIS_SEP.join(pb)


def rows(doc):
    for region in doc.get("regions", []):
        law = (region.get("law") or {}).get("citation", "")
        for m in region.get("mappings", []):
            yield {
                "region": region.get("region", ""),
                "ine_ca_code": region.get("ine_ca_code", ""),
                "law": law,
                "local_term": m.get("local", ""),
                "local_term_es": m.get("local_es", ""),
                "local_code": m.get("local_code", ""),
                "canonical": m.get("canonical", ""),
                "article": m.get("article", ""),
                "legacy": m.get("legacy", False),
                "label_abolished": m.get("label_abolished", False),
                "flag": m.get("flag", ""),
                "protection_basis": _basis(m),
                # Absent is not False here: `rural_settlement: false` is written
                # deliberately on the rows that look like settlements and are not
                # (Murcia art. 84.2, Valencia ZUR-NH), and blank means the
                # question was never asked of that row.
                "rural_settlement": m.get("rural_settlement", ""),
                "settlement_position": m.get("settlement_position", ""),
                "valid_from": m.get("valid_from", ""),
                "valid_to": m.get("valid_to", ""),
                "confidence": region.get("confidence", ""),
                "verified_at_version": region.get("verified_at_version", ""),
            }


def render(doc):
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=COLUMNS, lineterminator="\n")
    w.writeheader()
    for row in rows(doc):
        w.writerow(row)
    return out.getvalue()

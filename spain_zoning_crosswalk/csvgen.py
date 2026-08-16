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

COLUMNS = [
    "region", "ine_ca_code", "law", "local_term", "local_term_es", "canonical",
    "article", "legacy", "label_abolished", "flag", "confidence",
    # NOT `crosswalk_version`. That name was read two ways — the version of this
    # FILE and the version at which this ROW was last established — and the two
    # differ for every region nobody has re-checked since 0.1.1-draft. See
    # README.
    "verified_at_version",
]


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
                "canonical": m.get("canonical", ""),
                "article": m.get("article", ""),
                "legacy": m.get("legacy", False),
                "label_abolished": m.get("label_abolished", False),
                "flag": m.get("flag", ""),
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

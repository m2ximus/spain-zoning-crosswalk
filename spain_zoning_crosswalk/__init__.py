"""Axis-1 land-classification crosswalk for Spain, as an importable package.

The data files are the product; this module is only a loader. Consumers should
record :func:`version` alongside any resolved answer, so a stored zoning result
can always be traced back to the exact crosswalk vintage that produced it.

    >>> import spain_zoning_crosswalk as x
    >>> doc = x.load()
    >>> len(doc["regions"])
    17

NOTHING HERE IS LEGAL ADVICE. Regions carrying confidence 'needs_review' have
not been checked against the BOE consolidated text — see the YAML header.
"""
from __future__ import annotations

import importlib.resources as _resources
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _dist_version
from typing import Any

import yaml

__all__ = ["load", "version", "DATA_DIR", "AXIS1"]

DATA_DIR = "crosswalks"
AXIS1 = "axis1-land-classification.yaml"


def load(name: str = AXIS1) -> dict[str, Any]:
    """Return the parsed crosswalk document.

    Reads through importlib.resources so it works from a wheel, a zipimport or
    an editable install alike -- never assume a filesystem path.
    """
    ref = _resources.files(__name__).joinpath(DATA_DIR, name)
    with ref.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def version() -> str:
    """Return the installed distribution version, e.g. ``"0.1.2"``.

    Falls back to the ``meta.version`` recorded inside the data file when the
    package is being used from a source tree that was never pip-installed.
    """
    try:
        return _dist_version("spain-zoning-crosswalk")
    except PackageNotFoundError:
        return str(load().get("meta", {}).get("version", "unknown"))

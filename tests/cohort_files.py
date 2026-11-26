"""Read patients straight from the committed bundles: the independent side of every check."""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

from synthetic_cohort import bundle_dir

Resource = dict[str, Any]


def patient_resources() -> Iterator[Resource]:
    """The Patient of each patient bundle (hospital and practitioner bundles have none)."""
    for path in sorted(bundle_dir().glob("*.json")):
        for entry in json.loads(path.read_text()).get("entry", []):
            resource = entry.get("resource", {})
            if resource.get("resourceType") == "Patient":
                yield resource

"""The cohort manifest: how the data was made, and a hash of every file made.

A unit test compares the committed files against it, so a data change can't slip in unnoticed
(it would silently change the consumers' test data and ground truth; spec §6).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from synthetic_cohort._members import SEED, read_members, state_counts


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_hashes(bundle_dir: Path) -> dict[str, dict[str, Any]]:
    return {
        p.name: {"sha256": sha256_file(p), "bytes": p.stat().st_size}
        for p in sorted(bundle_dir.glob("*.json"))
    }


def members_entry(path: Path) -> dict[str, Any]:
    members = read_members(path)
    return {"seed": SEED, "counts": state_counts(members), "sha256": sha256_file(path)}


def write_manifest(generation: dict[str, Any], data_dir: Path) -> None:
    files = file_hashes(data_dir / "bundles")
    body = {
        "generation": generation,
        "total_bytes": sum(f["bytes"] for f in files.values()),
        "files": files,
        "members": members_entry(data_dir / "members.json"),
    }
    (data_dir / "manifest.json").write_text(json.dumps(body, indent=2, sort_keys=True) + "\n")


def read_manifest(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = json.loads(path.read_text())
    return data

"""Generate the pinned cohort with Synthea. Only needed to change the cohort.

Synthea runs from its released jar inside a pinned JRE container, so no local Java is needed and
every run uses the same Java. The jar is downloaded once to .cache/ and its sha256 checked before
it's used. Everything is built in a temporary directory and moved into the package only once all
of it has succeeded.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from synthetic_cohort._manifest import sha256_file, write_manifest
from synthetic_cohort._members import (
    Period,
    derive_members,
    read_patients,
    read_periods,
    write_members,
)
from synthetic_cohort._paths import DATA_DIR, KEEP_MODULE, PROPERTIES

SYNTHEA_VERSION = "4.0.0"
SYNTHEA_JAR_URL = (
    "https://github.com/synthetichealth/synthea/releases/download/"
    f"v{SYNTHEA_VERSION}/synthea-with-dependencies.jar"
)
SYNTHEA_JAR_SHA256 = "ed43c20ad40ba5c3bc724503a5af032715fe3c491620b766148e7c2361e6ecc1"
JRE_IMAGE = (
    "eclipse-temurin:21.0.12.1_1-jre-noble"
    "@sha256:cd35bb33859641c5374415826a5951845104093eaa401cbe9d3d9023444f1c13"
)
# Fixed so that ages, dates and "five years of history" don't move with the calendar.
REFERENCE_DATE = "20261101"
STATE = "Massachusetts"


@dataclass(frozen=True)
class Run:
    name: str
    seed: int
    clinician_seed: int
    population: int
    keep_module: str | None


RUNS = (
    # A general population: non-respiratory patients for fact, list and absent cases.
    Run("general", seed=1122, clinician_seed=1122, population=15, keep_module=None),
    # Respiratory-enriched: only patients with active asthma or COPD at the reference date.
    Run("resp", seed=2211, clinician_seed=2211, population=20, keep_module=KEEP_MODULE.name),
)


def checkout_root(package_dir: Path | None = None) -> Path:
    """The repository root. Refuses from an installed copy: generate rewrites the package data."""
    package = package_dir or Path(__file__).resolve().parent
    root = package.parent.parent
    pyproject = root / "pyproject.toml"
    if (
        package.parent.name != "src"
        or not pyproject.is_file()
        or 'name = "synthetic-cohort"' not in pyproject.read_text()
    ):
        raise RuntimeError("generate only runs from a checkout of the synthetic-cohort repo")
    return root


def ensure_jar(cache_dir: Path) -> Path:
    jar = cache_dir / f"synthea-{SYNTHEA_VERSION}.jar"
    if not jar.exists():
        cache_dir.mkdir(parents=True, exist_ok=True)
        partial = jar.with_suffix(".part")
        # A fixed https URL, and the bytes are checked against the pinned hash below.
        with (
            urllib.request.urlopen(SYNTHEA_JAR_URL, timeout=600) as response,  # noqa: S310
            partial.open("wb") as f,
        ):
            shutil.copyfileobj(response, f)
        partial.rename(jar)
    actual = sha256_file(jar)
    if actual != SYNTHEA_JAR_SHA256:
        jar.unlink()
        raise RuntimeError(f"Synthea jar sha256 mismatch: got {actual}, deleted it")
    return jar


def synthea_command(run: Run, jar: Path, out_dir: Path) -> list[str]:
    cmd = [
        "docker", "run", "--rm",
        "--user", f"{os.getuid()}:{os.getgid()}",
        "-e", "HOME=/tmp",
        "-v", f"{jar}:/synthea.jar:ro",
        "-v", f"{DATA_DIR}:/cohort:ro",
        "-v", f"{out_dir}:/out",
        "-w", "/out",
        JRE_IMAGE,
        "java", "-jar", "/synthea.jar",
        "-s", str(run.seed),
        "-cs", str(run.clinician_seed),
        "-r", REFERENCE_DATE,
        # Stop the simulation at the reference date too. Without this Synthea runs to the wall
        # clock: records get events after the reference date, and an encounter still open at the
        # end gets "now" as its end time, so no two runs match.
        "-e", REFERENCE_DATE,
        "-p", str(run.population),
        "-c", f"/cohort/{PROPERTIES.name}",
        "--exporter.baseDirectory=/out/",
        # Payer data for members.json (ADR 0003). A flag, so the settings file doesn't change.
        "--exporter.csv.export=true",
    ]  # fmt: skip
    if run.keep_module:
        cmd += ["-k", f"/cohort/{run.keep_module}"]
    cmd.append(STATE)
    return cmd


def collect(run: Run, out_dir: Path, dest: Path) -> None:
    """Copy one run's bundles into `dest`, prefixed by run name, with stable file names."""
    for src in sorted((out_dir / "fhir").glob("*.json")):
        name = src.name
        for shared in ("hospitalInformation", "practitionerInformation"):
            if name.startswith(shared):
                name = f"{shared}.json"  # Synthea appends a timestamp; drop it
        shutil.copyfile(src, dest / f"{run.name}-{name}")


def generate() -> None:
    root = checkout_root()
    jar = ensure_jar(root / ".cache" / "synthea")
    reference = datetime.strptime(REFERENCE_DATE, "%Y%m%d").date()
    with tempfile.TemporaryDirectory(prefix="synthetic-cohort-") as tmp:
        staged = Path(tmp) / "data"
        bundles = staged / "bundles"
        bundles.mkdir(parents=True)
        periods: list[Period] = []
        for run in RUNS:
            out = Path(tmp) / run.name
            out.mkdir()
            subprocess.run(synthea_command(run, jar, out), check=True)  # noqa: S603 - fixed argv
            collect(run, out, bundles)
            periods += read_periods(out / "csv")
        members = derive_members(read_patients(bundles), periods, reference)
        write_members(members, reference, staged / "members.json")
        write_manifest(
            {
                "synthea_version": SYNTHEA_VERSION,
                "synthea_jar_sha256": SYNTHEA_JAR_SHA256,
                "jre_image": JRE_IMAGE,
                "reference_date": REFERENCE_DATE,
                "state": STATE,
                "properties_sha256": sha256_file(PROPERTIES),
                "keep_module_sha256": sha256_file(KEEP_MODULE),
                "runs": [asdict(run) for run in RUNS],
            },
            staged,
        )
        shutil.rmtree(DATA_DIR / "bundles", ignore_errors=True)
        shutil.copytree(bundles, DATA_DIR / "bundles")
        for name in ("members.json", "manifest.json"):
            shutil.copyfile(staged / name, DATA_DIR / name)

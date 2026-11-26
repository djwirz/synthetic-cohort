# synthetic-cohort

One shared set of synthetic patients for several projects: FHIR R4 bundles generated with Synthea, a manifest of their hashes, a `members.json` saying what a payer would know about each patient's coverage, and the tooling that generates and checks them. The same inputs give the same bytes.

**Status:** released as `v0.1.0`. Design: [docs/spec.md](docs/spec.md) and [docs/adr/](docs/adr/).

## Use it

Add it pinned to a tag:

```bash
uv add "synthetic-cohort @ git+https://github.com/djwirz/synthetic-cohort" --tag v0.1.0
```

| Name | Gives |
|---|---|
| `synthetic_cohort.bundle_dir()` | path to the bundle files |
| `synthetic_cohort.manifest()` | how the data was made, and its hashes |
| `synthetic_cohort.patients()` | each patient's id, name, birth date and bundle path |
| `synthetic_cohort.members()` | each patient's payer, member id, coverage period and state ([spec §5](docs/spec.md#5-membersjson)) |
| `synthetic_cohort.check` | `check`, `summarise_bundle`, `ASTHMA_CODES`, `COPD_CODES` |

See what the cohort contains (from a checkout, or a project that depends on it):

```bash
uv run synthetic-cohort check
```

## What's in it

In `src/synthetic_cohort/data/`:

| File | What it is |
|---|---|
| `bundles/` | `general-*` and `resp-*` patient bundles, plus each run's hospital and practitioner bundles |
| `members.json` | one coverage entry per patient |
| `manifest.json` | how the data was made, and the sha256 of each generated file. A test checks them. |
| `synthea.properties` | Synthea settings that differ from its defaults |
| `keep_respiratory.json` | the keep filter for the respiratory run: active asthma or COPD |

The settings were moved byte for byte from fhir-over-mcp, so the ADR numbers in their comments are [that repo's](https://github.com/djwirz/fhir-over-mcp/tree/main/docs/adr).

## Regenerate it (only to change the data)

From a checkout, with Docker running:

```bash
uv run synthetic-cohort generate
```

This downloads the Synthea jar once to `.cache/` and checks its sha256, runs Synthea in a pinned JRE container (no local Java needed), and replaces the bundles, `members.json` and `manifest.json`. A data change is a new version ([ADR 0002](docs/adr/0002-one-shared-cohort-repo.md)).

Used by (planned):
- [fhir-over-mcp](https://github.com/djwirz/fhir-over-mcp): the bundles, as FHIR server data and eval ground truth.
- coverage-check: `members.json`, the members behind its mock payer and its check batches.

Synthetic data only. No real patient, member or payer data. Insurer names in the data come from Synthea's built-in payer list; the members, plans and coverage are made up.

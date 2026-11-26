# synthetic-cohort: spec

Status: Draft for PR #1 · Date: 2026-11-26 · Owner: Dan

## 1. Problem

Two projects need synthetic patients. FHIR over MCP has a pinned, reproducible Synthea cohort inside its repo. Coverage Check needs insurance members with a range of coverage states. If each makes its own:
- the two tell unrelated stories, with different people;
- the work that makes generation reproducible (pinned versions, seeds, end date, one thread) gets copied or redone;
- a change to one copy silently stops matching the other.

synthetic-cohort owns all of the synthetic-patient work once: settings, seeds, data, hashes and tooling. Projects depend on a tagged version and get the same people.

## 2. Non-goals

- **Loading or serving data.** No server, no API service, no database. The HAPI loader stays in FHIR over MCP.
- **Real data.** Synthea output only.
- **Project-specific data.** Eval cases, ground truth, check batches, failure profiles and payer behaviour belong to the consumers.
- **Load-test volume.** The cohort is a few dozen people. A consumer that needs thousands of requests builds them itself.
- **Claims, benefits or plan detail.** Members carry a payer, a member id and a coverage period, nothing more.
- **Publishing to a package index.** A git tag is enough.

## 3. What it holds

```
src/synthetic_cohort/
  data/
    bundles/                 FHIR R4 transaction bundles
    members.json             one entry per patient (§5)
    manifest.json            generation settings and a sha256 of every data file
    synthea.properties       settings that differ from Synthea's defaults
    keep_respiratory.json    keep filter for the respiratory run
  generate.py  members.py  manifest.py  check.py  cli.py
tests/
```

The data lives inside the package because a git dependency installs the package, not the repository (ADR 0002).

The bundles are FHIR over MCP's, moved unchanged: Synthea v4.0.0 run in a pinned JRE container, a general run (15 patients, seed 1122) and a respiratory run (20 patients with active asthma or COPD, seed 2211), reference and end date 2026-11-01, Massachusetts, living patients, five years of history, billing and document resources left out, one generator thread. The reasoning is in FHIR over MCP's [ADR 0003](https://github.com/djwirz/fhir-over-mcp/blob/main/docs/adr/0003-pinned-synthea-cohort-in-local-hapi.md) and [ADR 0007](https://github.com/djwirz/fhir-over-mcp/blob/main/docs/adr/0007-cohort-composition.md), carried over by ADR 0002.

## 4. Interfaces

**Python**, no runtime dependencies:

| Name | Gives |
|---|---|
| `synthetic_cohort.bundle_dir()` | path to the bundle files |
| `synthetic_cohort.manifest()` | the parsed manifest |
| `synthetic_cohort.patients()` | each patient's Synthea id, name, birth date and bundle path |
| `synthetic_cohort.members()` | the parsed `members.json` entries |
| `synthetic_cohort.check` | `check`, `summarise_bundle`, `ASTHMA_CODES`, `COPD_CODES`, as FHIR over MCP uses them today |

**CLI:**
- `synthetic-cohort check`: what the cohort contains (patients, conditions, inhalers, lung-function readings, coverage states).
- `synthetic-cohort generate`: rebuild the data. Needs Docker and a checkout of this repo. Only for changing the cohort.

**As a dependency**, pinned to a tag:

```bash
uv add "synthetic-cohort @ git+https://github.com/djwirz/synthetic-cohort" --tag v0.1.0
```

## 5. members.json

What a caller holds about each patient's insurance, and what a payer should say about it. Coverage Check seeds its mock payer and its batches from it. The design and why: ADR 0003.

```json
{
  "reference_date": "2026-11-01",
  "members": [
    {
      "patient_id": "<Synthea UUID>",
      "given": ["<given name>"],
      "family": "<family name>",
      "birth_date": "<YYYY-MM-DD>",
      "payer": "<payer name from Synthea>",
      "member_id": "<member id from Synthea>",
      "coverage_start": "<YYYY-MM-DD>",
      "coverage_end": "<YYYY-MM-DD>",
      "coverage_state": "covered | inactive | missing | ambiguous",
      "source": "synthea | assigned"
    }
  ]
}
```

| State | Meaning, as of the reference date | Where it comes from |
|---|---|---|
| `covered` | coverage is active | Synthea |
| `inactive` | the payer knows the member; coverage has ended | Synthea where its records show it, topped up by assignment |
| `missing` | the payer has no such member | assigned |
| `ambiguous` | the payer finds more than one match | assigned |

Every patient has one entry. There are a handful (four) of each state other than `covered`, and the rest are covered. `source` is `assigned` when the state was chosen by this repo's code and not by Synthea.

How a consumer turns a state into behaviour (for example, how the mock payer produces a second match) is its own business.

## 6. Invariants and failure modes

1. **Byte-identical:** regenerating with the pinned inputs gives the same bundles and `members.json`.
2. **Manifest matches:** the committed files match the manifest's hashes.
3. **Synthetic only:** everything comes from Synthea or is derived from it by seeded code.
4. **Same people:** every member's id, name and birth date equal those in that patient's bundle.
5. **Tags don't move:** a released version always means the same data.

| Failure | What happens |
|---|---|
| A data file is changed, added or removed by hand | The manifest test fails in CI. |
| The downloaded Synthea jar isn't the pinned one | Generation deletes it and stops. |
| `generate` is run from an installed copy, not a checkout | It refuses. |
| Regeneration gives different bytes | Treated as a bug. Nothing is released until it's explained. |
| Too few covered patients to assign the other states, or a patient with no payer record | Generation stops with an error. |
| A consumer wants different data | A new tag. Consumers move when they choose to. |

## 7. Testing and CI

- **Unit:** the manifest check; the member derivation on small made-up inputs (each state, each rule, the same output twice); every state present in the committed `members.json`; members matching their bundles; the cohort still holding what FHIR over MCP's eval needs; the size guard.
- **Reproducibility:** `generate` takes minutes and needs Docker, so it isn't run on every PR. A PR that touches data or generation reports a fresh regeneration with no diff.
- **CI on every PR:** ruff, mypy, pytest, gitleaks.

## 8. Acceptance criteria (v0.1.0)

1. Every bundle's sha256 equals the one in FHIR over MCP's `cohort/manifest.json` as of this spec, both as committed and after a fresh regeneration here.
2. `members.json` regenerates identically, covers all 35 patients, and holds every state.
3. A scratch project that adds the tag with uv can read the bundles, patients and members.
4. CI is green and `v0.1.0` is tagged on `main`.

## 9. Slice plan

1. **Move and publish** (one PR): the uv project, tooling and data moved from FHIR over MCP, `members.json`, tests, CI. Then tag `v0.1.0`.

Then, in the consuming repos:
- **FHIR over MCP**, after its slice 2 merges: depend on the tag, delete the moved code and data, keep `cohort load`.
- **Coverage Check**, slice 1: depend on the tag, read `members.json`.

## 10. Open questions

None block slice 1. For the consumers:
- **Coverage Check's batch size.** It plans batches of a few thousand checks; there are 35 members. Repeating members or adding load-only ones is its decision.
- **Real insurer names.** Synthea's payers include real company names. If a consumer would rather not show them, mapping them to made-up names is a data change here (new ADR, new tag).

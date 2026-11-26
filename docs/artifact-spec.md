# Artifact spec: synthetic-cohort

Draft for PR #1, 2026-11-26. Short on purpose: this is shared groundwork, not a showcase project.

## One line
One reproducible set of synthetic patients, with their records and coverage states, that several projects share by pinning a version.

## What it exercises
Python packaging, FHIR R4, reproducible data generation. A result of the design, not a target.

## Problem and users
- **Who has the problem:** Dan's projects (FHIR over MCP now, Coverage Check next) and whoever reads them.
- **Today:** the cohort lives inside one project; the next would make its own.
- **Why it matters:** evals and tests only compare across runs if the data is pinned, and the two projects only tell one story if the people are the same.

## Scope
- **Must have:** the existing cohort moved with identical bytes; `members.json` with all four coverage states; hashes checked in CI; installable from a tag.
- **Non-goals:** servers, loaders, real data, volume data, benefits or claims, a package index release (spec §2).

## Success metric
Both consumers run on the same tag, FHIR over MCP's tests and ground truth pass unchanged, and the same patient ids appear in both.

## Constraints
- **Time:** a session or two.
- **Budget:** nothing.
- **Data:** Synthea only.

## Quality plan
Unit tests and a manifest check in CI, gitleaks, and a fresh regeneration for any data change (spec §7).

## Depth target
Rung 2: tested and used by other projects. Nothing is deployed.

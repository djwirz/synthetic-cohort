# synthetic-cohort

One shared set of synthetic patients for several projects: FHIR R4 bundles generated with Synthea, a manifest of their hashes, a `members.json` saying what a payer would know about each patient's coverage, and the tooling that generates and checks them. The same inputs give the same bytes.

**Status:** planning. Nothing is here to install yet. Design: [docs/spec.md](docs/spec.md) and [docs/adr/](docs/adr/).

Used by (planned):
- [fhir-over-mcp](https://github.com/djwirz/fhir-over-mcp): the bundles, as FHIR server data and eval ground truth.
- coverage-check: `members.json`, the members behind its mock payer and its check batches.

Synthetic data only. No real patient, member or payer data. Insurer names in the data come from Synthea's built-in payer list; the members, plans and coverage are made up.

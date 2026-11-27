# synthetic-cohort: instructions for Claude

One shared, byte-reproducible set of synthetic patients for Dan's projects: Synthea FHIR bundles, a manifest of their hashes, a `members.json` of coverage states, and the tooling that makes and checks them. FHIR over MCP uses the bundles and Coverage Check uses the members, so both tell one story with the same people. Use they/them for Dan.

## Status
`v0.1.0` is released: slice 1 (spec §9) moved the data and tooling here and added `members.json`. The consumers move to that tag in their own repos. Decisions: `docs/spec.md` and `docs/adr/`. The judgment behind the project is in `docs/artifact-spec.md`.

Check a change with `uv run ruff check`, `uv run ruff format --check`, `uv run mypy` and `uv run pytest`.

## How we work
- Pull requests only. Never push to `main`. Merged PRs are the project's record.
- Spec first, then one thin end-to-end slice per PR (spec §9). Start each slice in plan mode.
- **Problem first, and keep it small.** This is a data package and the script that builds it. Add something only when a consumer or an invariant needs it.
- Every decision that would be expensive to reverse gets an ADR in `docs/adr/` (format: ADR 0001). Don't decide quietly in code.
- ADRs are written as `Accepted` in the PR that adds them, and merging is the acceptance. Never rewrite a merged ADR's decision. Add a new ADR that supersedes it.
- When the spec and the code disagree, stop and ask. If the decision changes, update the spec in the same PR.
- A change to any bundle or to `members.json` changes the consumers' test data and eval ground truth. Say so in the PR and release it as a new version.
- Built with Claude Code. Note real mistakes in PR descriptions.

## Constraints
- Never employer code, data or names beyond what's public. Synthetic data only (Synthea).
- Python 3.12 with uv, ruff, mypy (strict) and pytest. No runtime dependencies (ADR 0002).
- Free tiers only. Nothing here needs hosting.
- Secrets never in the repo, logs or PR text.
- Numbers in docs: honest estimates in words, never false precision. Counts read from the committed data are exact.

## Invariants (spec §6): never break these
1. **Byte-identical:** regenerating with the pinned inputs gives the same bundles and `members.json`.
2. **Manifest matches:** the committed files match the manifest's hashes.
3. **Synthetic only:** everything comes from Synthea or is derived from it by seeded code.
4. **Same people:** every member's id, name and birth date equal those in that patient's bundle.
5. **Tags don't move:** a released version always means the same data.

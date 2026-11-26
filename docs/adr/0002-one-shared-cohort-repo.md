# 2. One shared cohort repo, consumed as a git dependency on a tag

Date: 2026-11-26
Status: Accepted

## Context
FHIR over MCP has a byte-reproducible Synthea cohort in its repo (its ADRs [0003](https://github.com/djwirz/fhir-over-mcp/blob/main/docs/adr/0003-pinned-synthea-cohort-in-local-hapi.md) and [0007](https://github.com/djwirz/fhir-over-mcp/blob/main/docs/adr/0007-cohort-composition.md)). Coverage Check needs synthetic members, ideally the same people. The bundles are about 24 MB.

## Options considered
1. **Each project makes its own.** No coupling, but different people, and the reproducibility work done twice.
2. **Coverage Check reads files from FHIR over MCP's repo.** Little work, but one project's internals become another's contract.
3. **A shared repo, consumed as a uv git dependency on a tag.** One owner for the data and tooling, versions pinned in each consumer's lockfile.
4. **A shared repo as a git submodule.** Files appear in the consumer's tree, but submodules are easy to leave stale, and the Python tooling still needs installing.
5. **Publish to a package index.** More release machinery than two consumers need.

## Decision
Option 3.
- This repo owns the Synthea settings, seeds, keep filter, committed bundles, manifest, and the `generate` and `check` tooling. FHIR over MCP's loader is HAPI-specific and stays there.
- The data sits inside the Python package, so installing the dependency installs the data.
- The package has no runtime dependencies. The one download (`generate` fetching the Synthea jar) uses the standard library.
- Releases are git tags, starting at `v0.1.0`. A tag is never moved or reused. Any change to a data file is a new version, said plainly in the PR.
- FHIR over MCP's choices in its ADRs 0003 and 0007 (what the cohort holds and how it's generated) carry over unchanged and are owned here from now on. Changing them takes an ADR in this repo.

## Why
It gives one owner and one history for the data, while each consumer decides when to move to a new version. A tag plus the lockfile's commit id is as reproducible as committing the files.

## Consequences
- Moving must not change a byte: every bundle's hash equals the one in FHIR over MCP's manifest.
- Consumers' first install downloads the repo and its data. A change that rewrites many bundles adds about that much again to the history.
- Reading the data now means installing a dependency; the files are no longer visible in the consumer's tree.
- FHIR over MCP keeps its old ADRs and adds one saying the cohort moved here. That happens in its own PR.
- `generate` writes into the package's data directory, so it runs only from a checkout.

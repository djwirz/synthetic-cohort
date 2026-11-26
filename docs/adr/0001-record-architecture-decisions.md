# 1. Record architecture decisions

Date: 2026-11-26
Status: Accepted

## Context
synthetic-cohort is built in the open with Claude Code, and other projects depend on its data. Decisions made in chat are lost, and decisions made silently in code are hard to review or explain later. Dan's other projects use ADRs.

## Options considered
1. **ADRs in the repo**, reviewed in pull requests like code.
2. **Decisions in PR descriptions only.** No extra files, but scattered and hard to find once merged.
3. **A single design doc kept up to date.** One place to read, but the history of why things changed is lost.

## Decision
Option 1. Every decision that would be expensive to reverse gets a short ADR in `docs/adr/`, numbered in order, with the sections Context, Options considered, Decision, Why and Consequences.

An ADR is written with `Status: Accepted` in the pull request that introduces it. The PR is where it's debated, and merging is the acceptance. A merged ADR isn't rewritten: to change a decision, a new ADR supersedes it, and the old one stays, marked "Superseded by N". Typos and broken links can be fixed in place.

## Why
It's the same practice as the other projects, so reviewers and later Claude sessions find decisions in the same place.

## Consequences
- The reasons behind the design survive the chat that produced them.
- A small cost per decision; trivial choices don't need one.

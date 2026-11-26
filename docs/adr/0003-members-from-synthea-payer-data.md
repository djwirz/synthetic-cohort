# 3. members.json: Synthea's payer data, plus assigned problem states

Date: 2026-11-26
Status: Accepted

## Context
Coverage Check needs members with a payer, a member id and a spread of coverage states, so that every outcome happens: covered, not covered, and exceptions a person has to work through. Its spec (§13 Q6) says to use Synthea's payer data if it turns out to be usable, and otherwise a small seeded generator.

What we found, by rerunning both seeded runs with `--exporter.csv.export=true` before writing this:
- The committed bundles hold no coverage: Claim and ExplanationOfBenefit are excluded.
- The CSV export's `payer_transitions.csv` has a payer, member id and coverage period for all 35 patients, and `payers.csv` names the payers.
- Turning CSV export on did not change the FHIR output: all 39 files matched FHIR over MCP's manifest.
- Both runs gave identical `payer_transitions.csv` and `payers.csv` when run a second time.
- At the reference date, 2026-11-01, 33 patients are covered. One is uninsured and one's last period ended just before the date. Synthea has nothing like "the payer can't find them" or "the payer finds two".

## Options considered
1. **Invent everything** with a seeded generator. Full control, but throws away data Synthea already gives.
2. **Synthea's data only.** Nothing invented, but no missing or ambiguous members and only two inactive.
3. **Synthea's payer, member id and period, with seeded assignment of the states Synthea doesn't give.**
4. **Put Coverage resources into the bundles.** Standard FHIR, but it changes every bundle hash and FHIR over MCP has no use for it.

## Decision
Option 3. `generate` turns CSV export on (a command-line flag, so the settings file and its hash don't change) and derives `members.json` (spec §5):
- One entry per patient: Synthea id, name and birth date from the bundle's Patient.
- Payer, member id and period from the latest period with a real payer (not `NO_INSURANCE`) that started on or before the reference date. `covered` if it includes the reference date (it starts on or before it and ends after it), otherwise `inactive`.
- Then, from the covered patients, ordered by a hash of a fixed seed and the patient id, assign enough to bring `inactive` up to four, then four `missing`, then four `ambiguous`.
- An assigned `inactive` member's end date is set to the day before the reference date, so the record agrees with the state. Only members whose period started before that day can be chosen.
- `source` says whether each state is Synthea's or assigned.
- The manifest records the seed, the counts and a sha256 of `members.json`, apart from the bundle entries.

## Why
It keeps what Synthea really generates, invents only what it can't, and says which is which. Hashing the id, rather than drawing from a random generator, gives the same choice on any Python version.

## Consequences
- Rebuilding `members.json` needs a Synthea run (Docker, a few minutes), because the CSV files aren't committed.
- Member ids are Synthea's, which are UUID-shaped and begin like the patient's id. They don't look like real insurance card numbers.
- Payer names are Synthea's defaults, which include real insurers. The people and their coverage are made up (spec §10).
- `missing` and `ambiguous` are labels. The consumer's mock payer has to make them happen.
- Changing the counts, seed or rules is a new version of the data.

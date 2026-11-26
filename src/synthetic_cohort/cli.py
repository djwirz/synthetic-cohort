"""Command line: `synthetic-cohort check` and `synthetic-cohort generate`."""

from __future__ import annotations

import argparse
import sys

from synthetic_cohort._members import read_members, state_counts
from synthetic_cohort._paths import MEMBERS
from synthetic_cohort.check import check


def _check() -> int:
    for line in check().lines():
        print(line)
    for state, count in state_counts(read_members(MEMBERS)).items():
        print(f"members {state}: {count}")
    return 0


def _generate() -> int:
    from synthetic_cohort.generate import generate

    generate()
    return _check()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="synthetic-cohort")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("check", help="summarise what the cohort contains").set_defaults(
        func=_check
    )
    commands.add_parser("generate", help="rebuild the data (Docker, repo checkout)").set_defaults(
        func=_generate
    )
    result: int = parser.parse_args(argv).func()
    return result


if __name__ == "__main__":
    sys.exit(main())

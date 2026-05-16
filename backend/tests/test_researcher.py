from __future__ import annotations

import argparse
import sys

from app.agents.researcher import ResearcherAgent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Phase 1 Researcher agent.")
    parser.add_argument(
        "task",
        nargs="?",
        default="top 3 Indian AI startups",
        help="Research task to send to the agent.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        output = ResearcherAgent().run(args.task)
    except Exception as exc:
        print(f"Researcher failed: {exc}", file=sys.stderr)
        return 1

    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

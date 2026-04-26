import argparse
import json

from config import DEFAULT_TOP_N
from filter_engine import run_candidate_filtering


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Phase 4 candidate retrieval and rule-based filtering."
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=DEFAULT_TOP_N,
        help=f"Number of shortlisted candidates to return (default: {DEFAULT_TOP_N}).",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    if args.top_n <= 0:
        raise ValueError("--top-n must be greater than 0.")
    metadata = run_candidate_filtering(top_n=args.top_n)
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()

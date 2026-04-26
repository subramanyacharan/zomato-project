import argparse
import json

from config import DEFAULT_TOP_N
from ranker import run_phase5


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Phase 5: LLM-powered ranking and explanation generation (Groq)."
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=DEFAULT_TOP_N,
        help=f"Maximum number of recommendations to generate (default: {DEFAULT_TOP_N}).",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run without Groq API call (for local validation).",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    if args.top_n <= 0:
        raise ValueError("--top-n must be greater than 0.")
    metadata = run_phase5(top_n=args.top_n, mock=args.mock)
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()

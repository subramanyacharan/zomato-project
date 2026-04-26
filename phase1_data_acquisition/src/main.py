import argparse
import json

from config import DEFAULT_SPLIT
from ingest import ingest_raw_snapshot


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Phase 1 ingestion: load Zomato dataset into staging storage."
    )
    parser.add_argument(
        "--split",
        default=DEFAULT_SPLIT,
        help="Dataset split to ingest (default: train).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    metadata = ingest_raw_snapshot(split=args.split)
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()

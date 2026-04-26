import argparse
import json
from pathlib import Path

from profile_builder import build_profile, save_profile


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Phase 3 preference collection and query normalization."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to user preference input JSON.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    payload = json.loads(input_path.read_text(encoding="utf-8"))
    validation_result = build_profile(payload)
    save_result = save_profile(validation_result)

    print(
        json.dumps(
            {
                "input_path": str(input_path.resolve()),
                "save_result": save_result,
                "warnings": validation_result.warnings,
                "errors": validation_result.errors,
                "normalized_profile": validation_result.normalized_profile,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

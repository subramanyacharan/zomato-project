import json

from preprocess import preprocess_phase2


def main() -> None:
    metadata = preprocess_phase2()
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()

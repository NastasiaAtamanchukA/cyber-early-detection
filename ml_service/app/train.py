import argparse

from app.model import train_model


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=str, default=None, help="Path to CSV with feature columns")
    args = parser.parse_args()
    bundle = train_model(csv_path=args.csv)
    print({"model_version": bundle["model_version"], "trained_on_rows": bundle["trained_on_rows"]})


if __name__ == "__main__":
    main()

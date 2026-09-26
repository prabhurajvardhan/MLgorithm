import pandas as pd
import re


def validate_dataset(file_path):

    print(f"\nValidating: {file_path}")

    df = pd.read_csv(file_path, sep="\t")

    print(f"Rows: {len(df):,}")
    print(f"Columns: {len(df.columns)}")

    # Missing values
    print("\nMissing values:")
    print(df.isnull().sum())

    # Duplicate rows
    print(f"\nDuplicate rows: {df.duplicated().sum():,}")

    # Duplicate entity IDs
    if "entity_id" in df.columns:
        print(
            f"Duplicate entity_id: "
            f"{df['entity_id'].duplicated().sum():,}"
        )

        valid_ids = df["entity_id"].str.match(
            r"^S\d+-\d+$",
            na=False
        )

        print(
            f"Invalid entity_id: "
            f"{(~valid_ids).sum():,}"
        )

    # String checks
    for column in ["business_name", "business_address"]:

        if column not in df.columns:
            continue

        # Leading/trailing spaces
        whitespace = (
            df[column].notna()
            & (df[column] != df[column].str.strip())
        )

        # Multiple spaces
        multiple_spaces = df[column].str.contains(
            r"\s{2,}",
            regex=True,
            na=False
        )

        # Control characters
        control_chars = df[column].str.contains(
            r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]",
            regex=True,
            na=False
        )

        # Encoding artifacts
        encoding_artifacts = df[column].str.contains(
            r"Â|â|ï¿½",
            regex=True,
            na=False
        )

        print(f"\n{column}:")
        print(
            f"Leading/trailing spaces: "
            f"{whitespace.sum():,}"
        )
        print(
            f"Multiple spaces: "
            f"{multiple_spaces.sum():,}"
        )
        print(
            f"Control characters: "
            f"{control_chars.sum():,}"
        )
        print(
            f"Encoding artifacts: "
            f"{encoding_artifacts.sum():,}"
        )

    print("\n-----------------------------------")


if __name__ == "__main__":

    normalized_files = [
        "data/train_source1_normalized.tsv",
        "data/train_source2_normalized.tsv",
        "data/train_source3_normalized.tsv"
    ]

    for file_path in normalized_files:
        validate_dataset(file_path)

    print("\nFinal validation completed.")
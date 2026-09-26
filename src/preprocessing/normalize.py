import pandas as pd
import yaml
import re
import os


# Load configuration
with open("configs/normalization.yaml", "r", encoding="utf-8") as file:
    config = yaml.safe_load(file)


def normalize_text(value):
    """Normalize a single text value."""

    if pd.isna(value):
        return value

    value = str(value)

    # Remove control characters
    value = re.sub(
        r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]",
        " ",
        value
    )

    # Repair common encoding artifacts
    encoding_replacements = {
        "\u00C2\u0080\u0093": "\u2013",
        "\u00C2\u0080\u0094": "\u2014",
        "\u00C2\u0080\u0099": "\u2019",
        "\u00C2\u0080\u0098": "\u2018",
        "\u00C2\u0080\u0090": "\u2010",
    }

    for bad, good in encoding_replacements.items():
        value = value.replace(bad, good)

    # Collapse multiple whitespace
    value = re.sub(r"\s+", " ", value)

    # Remove leading/trailing spaces
    value = value.strip()

    return value


def normalize_dataset(input_file, output_file):

    print(f"\nProcessing: {input_file}")

    # Read dataset
    df = pd.read_csv(input_file, sep="\t")

    original_rows = len(df)

    # Normalize text columns
    for column in ["business_name", "business_address"]:

        if column in df.columns:
            df[column] = df[column].apply(normalize_text)

    # Validate entity_id
    invalid_entity_ids = 0

    if "entity_id" in df.columns:

        valid_ids = df["entity_id"].str.match(
            r"^S\d+-\d+$",
            na=False
        )

        invalid_entity_ids = (~valid_ids).sum()

    # Save normalized dataset
    df.to_csv(
        output_file,
        sep="\t",
        index=False
    )

    print(f"Rows processed: {original_rows:,}")
    print(f"Invalid entity IDs: {invalid_entity_ids:,}")
    print(f"Saved: {output_file}")

    return {
        "input_file": input_file,
        "output_file": output_file,
        "rows": original_rows,
        "invalid_entity_ids": invalid_entity_ids
    }


if __name__ == "__main__":

    # Create reports directory if needed
    os.makedirs("reports", exist_ok=True)

    datasets = [
        (
            "data/train_source1.tsv",
            "data/train_source1_normalized.tsv"
        ),
        (
            "data/train_source2.tsv",
            "data/train_source2_normalized.tsv"
        ),
        (
            "data/train_source3.tsv",
            "data/train_source3_normalized.tsv"
        )
    ]

    experiments = []

    for input_file, output_file in datasets:

        result = normalize_dataset(
            input_file,
            output_file
        )

        experiments.append(result)

    # Create experiment report
    experiments_df = pd.DataFrame(experiments)

    experiments_df.to_csv(
        "reports/normalization_experiments.csv",
        index=False
    )

    print("\n===================================")
    print("Normalization completed.")
    print("Experiment report saved to:")
    print("reports/normalization_experiments.csv")
    print("===================================")
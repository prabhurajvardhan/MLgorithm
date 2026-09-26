import pandas as pd
import re


def profile_dataset(file_path):
    # Load dataset
    df = pd.read_csv(file_path, sep="\t")

    report = []

    # Basic information
    report.append(f"## Dataset: {file_path}\n")
    report.append(f"- Rows: {len(df):,}")
    report.append(f"- Columns: {len(df.columns)}")
    report.append(f"- Column names: {list(df.columns)}\n")

    # Data types
    report.append("## Data Types\n")
    report.append(df.dtypes.to_string())
    report.append("")

    # Missing values
    report.append("## Missing Values\n")
    missing = df.isnull().sum()
    report.append(missing.to_string())
    report.append("")

    # Duplicate rows
    report.append("## Duplicates\n")
    report.append(f"- Duplicate rows: {df.duplicated().sum():,}")

    if "entity_id" in df.columns:
        report.append(
            f"- Duplicate entity_id: "
            f"{df['entity_id'].duplicated().sum():,}"
        )

    report.append("")

    # Check string columns
    string_columns = [
        col for col in ["business_name", "business_address"]
        if col in df.columns
    ]

    report.append("## Whitespace Checks\n")

    for col in string_columns:

        # Leading/trailing spaces
        whitespace_check = (
            df[col].notna() &
            (df[col] != df[col].str.strip())
        )

        # Multiple spaces
        multiple_spaces = df[col].str.contains(
            r"\s{2,}",
            regex=True,
            na=False
        )

        report.append(
            f"- {col} leading/trailing spaces: "
            f"{whitespace_check.sum():,}"
        )

        report.append(
            f"- {col} multiple spaces: "
            f"{multiple_spaces.sum():,}"
        )

    report.append("")

    # Unicode / non-ASCII
    report.append("## Unicode Check\n")

    for col in string_columns:
        non_ascii = df[col].str.contains(
            r"[^\x00-\x7F]",
            regex=True,
            na=False
        ).sum()

        report.append(
            f"- {col} non-ASCII records: {non_ascii:,}"
        )

    report.append("")

    # Control characters
    report.append("## Control Characters\n")

    control_pattern = r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]"

    for col in string_columns:
        control_chars = df[col].str.contains(
            control_pattern,
            regex=True,
            na=False
        ).sum()

        report.append(
            f"- {col} control-character records: "
            f"{control_chars:,}"
        )

    report.append("")

    # Encoding artifacts
    report.append("## Encoding Artifacts\n")

    encoding_pattern = r"Â|â|ï¿½"

    for col in string_columns:
        encoding_artifacts = df[col].str.contains(
            encoding_pattern,
            regex=True,
            na=False
        ).sum()

        report.append(
            f"- {col} possible encoding-artifact records: "
            f"{encoding_artifacts:,}"
        )

    report.append("")

    # Entity ID validation
    if "entity_id" in df.columns:

        report.append("## Entity ID Validation\n")

        pattern_check = df["entity_id"].str.match(
            r"^S\d+-\d+$",
            na=False
        )

        report.append(
            f"- Valid entity_id: {pattern_check.sum():,}"
        )

        report.append(
            f"- Invalid entity_id: "
            f"{(~pattern_check).sum():,}"
        )

        report.append("")

    # Country distribution
    if "country" in df.columns:

        report.append("## Country Distribution\n")

        country_counts = df["country"].value_counts(
            dropna=False
        )

        report.append(country_counts.to_string())
        report.append("")

    # Duplicate business name + address
    if all(
        col in df.columns
        for col in ["business_name", "business_address"]
    ):

        duplicate_businesses = df.duplicated(
            subset=["business_name", "business_address"],
            keep=False
        )

        report.append("## Duplicate Business Name + Address\n")

        report.append(
            f"- Records belonging to duplicate "
            f"name + address groups: "
            f"{duplicate_businesses.sum():,}"
        )

        unique_businesses = df.drop_duplicates(
            subset=["business_name", "business_address"]
        )

        report.append(
            f"- Unique name + address combinations: "
            f"{len(unique_businesses):,}"
        )

        report.append("")

    # Country conflicts
    if all(
        col in df.columns
        for col in ["business_name", "business_address", "country"]
    ):

        country_conflicts = (
            df.groupby(
                ["business_name", "business_address"],
                dropna=False
            )["country"]
            .nunique()
        )

        report.append("## Country Conflicts\n")

        report.append(
            f"- Name + address combinations with "
            f"multiple countries: "
            f"{(country_conflicts > 1).sum():,}"
        )

        report.append("")

    return "\n".join(report)


if __name__ == "__main__":

    datasets = [
    "data/train_source1.tsv",
    "data/train_source2.tsv",
    "data/train_source3.tsv"
]

    all_reports = []

    for dataset in datasets:

        try:
            result = profile_dataset(dataset)
            all_reports.append(result)

        except FileNotFoundError:
            print(f"File not found: {dataset}")

    # Save report
    with open(
        "reports/data_profile.md",
        "w",
        encoding="utf-8"
    ) as file:

        file.write("\n\n".join(all_reports))

    print("Data profiling completed.")
    print("Report saved to reports/data_profile.md")

import pandas as pd

from .features import build_pair_features


def load_ground_truth(file_path):
    """Load ground truth and convert matched IDs into sets."""

    ground_truth = pd.read_csv(file_path, sep="\t")

    ground_truth["matched_entity_ids"] = (
        ground_truth["matched_entity_ids"]
        .fillna("")
        .apply(
            lambda x: set(
                item.strip()
                for item in x.split(",")
                if item.strip()
            )
        )
    )

    return ground_truth


def create_training_data(
    s1,
    s2,
    s3,
    candidate_pairs,
    ground_truth
):
    """Create feature data and labels from candidate pairs."""

    s1_records = s1.set_index("entity_id").to_dict("index")
    s2_records = s2.set_index("entity_id").to_dict("index")
    s3_records = s3.set_index("entity_id").to_dict("index")

    ground_truth = ground_truth.set_index("source1_entity_id")

    training_rows = []

    for _, pair in candidate_pairs.iterrows():

        s1_id = pair["source1_entity_id"]
        candidate_id = pair["candidate_entity_id"]

        s1_row = s1_records[s1_id]

        if candidate_id.startswith("S2-"):
            candidate_row = s2_records[candidate_id]
        else:
            candidate_row = s3_records[candidate_id]

        features = build_pair_features(
            s1_row,
            candidate_row
        )

        if s1_id in ground_truth.index:
            matched_ids = ground_truth.loc[
                s1_id, "matched_entity_ids"
            ]
        else:
            matched_ids = set()

        if candidate_id in matched_ids:
            label = 1
        else:
            label = 0

        features["label"] = label
        features["source1_entity_id"] = s1_id
        features["candidate_entity_id"] = candidate_id

        training_rows.append(features)

    return pd.DataFrame(training_rows)


import pandas as pd


def create_matching_results(
    predictions_df,
    s1,
    threshold=0.5
):
    """
    Convert match probabilities into final matched IDs.
    """

    results = []

    for _, s1_row in s1.iterrows():

        s1_id = s1_row["entity_id"]

        rows = predictions_df[
            predictions_df["source1_entity_id"] == s1_id
        ]

        matched_ids = []

        for _, row in rows.iterrows():

            if row["match_probability"] >= threshold:
                matched_ids.append(
                    row["candidate_entity_id"]
                )

        results.append({
            "source1_entity_id": s1_id,
            "matched_entity_ids": ",".join(matched_ids)
        })

    return pd.DataFrame(results)

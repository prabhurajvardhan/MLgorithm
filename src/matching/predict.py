
import joblib

from .features import build_pair_features


def predict_pairs(
    s1,
    s2,
    s3,
    candidate_pairs,
    model_path
):
    """Predict match probability for every candidate pair."""

    model = joblib.load(model_path)

    s1_records = s1.set_index("entity_id").to_dict("index")
    s2_records = s2.set_index("entity_id").to_dict("index")
    s3_records = s3.set_index("entity_id").to_dict("index")

    feature_columns = [
        "name_jaccard",
        "name_levenshtein",
        "name_token_sort",
        "name_exact",
        "address_jaccard",
        "address_levenshtein",
        "address_token_sort",
        "address_exact",
        "country_match"
    ]

    results = []

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

        X = [features[column] for column in feature_columns]

        probability = model.predict_proba([X])[0][1]

        results.append({
            "source1_entity_id": s1_id,
            "candidate_entity_id": candidate_id,
            "match_probability": probability
        })

    return results

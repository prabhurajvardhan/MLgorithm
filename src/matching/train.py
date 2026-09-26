
import os
import joblib

from .model import create_model


def train_model(training_data, model_path):
    """Train XGBoost using the generated training data."""

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

    X = training_data[feature_columns]
    y = training_data["label"]

    model = create_model()

    model.fit(X, y)

    os.makedirs(os.path.dirname(model_path), exist_ok=True)

    joblib.dump(model, model_path)

    print("Model trained successfully.")
    print("Training samples:", len(X))
    print("Features:", len(feature_columns))
    print("Model saved to:", model_path)

    return model


from xgboost import XGBClassifier


def create_model():
    """Create the XGBoost classification model."""

    model = XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        random_state=42,
        eval_metric="logloss"
    )

    return model

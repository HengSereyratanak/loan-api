"""Train the model and save it to model/loan_model.joblib."""

from pathlib import Path

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

FEATURES = ["income", "loan_amount", "term_months", "credit_score", "employment_years"]
VERSION = "1.0.0"
OUTPUT = Path("model/loan_model.joblib")


def make_data(n: int = 5000, seed: int = 42):
    rng = np.random.default_rng(seed)
    income = rng.lognormal(mean=7.0, sigma=0.5, size=n)
    loan_amount = rng.uniform(300, 20000, size=n)
    term_months = rng.integers(6, 61, size=n)
    credit_score = rng.integers(300, 851, size=n)
    employment_years = rng.uniform(0, 30, size=n)

    monthly_payment = loan_amount / term_months
    burden = monthly_payment / income
    logit = (
        4.0 * burden
        - 0.012 * (credit_score - 600)
        - 0.08 * employment_years
        - 0.5
    )
    default = rng.random(n) < 1 / (1 + np.exp(-logit))

    X = np.column_stack([income, loan_amount, term_months, credit_score, employment_years])
    return X, default.astype(int)


def main() -> None:
    X, y = make_data()
    model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
    model.fit(X, y)
    print(f"Training accuracy: {model.score(X, y):.3f}")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "features": FEATURES, "version": VERSION}, OUTPUT)
    print(f"Saved {OUTPUT}")


if __name__ == "__main__":
    main()

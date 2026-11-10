"""Loan prediction API."""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

import joblib
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

MODEL_PATH = os.getenv("MODEL_PATH", "model/loan_model.joblib")
DATABASE_URL = os.getenv("DATABASE_URL")

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("loan-api")

state: dict = {}


def load_model(path: str) -> dict:
    model_file = Path(path)
    if not model_file.is_file():
        raise RuntimeError(f"Model file not found at MODEL_PATH={path}")
    bundle = joblib.load(model_file)
    logger.info("Loaded model %s from %s", bundle["version"], path)
    return bundle


@asynccontextmanager
async def lifespan(app: FastAPI):
    state["model"] = load_model(MODEL_PATH)
    yield
    state.clear()


app = FastAPI(
    title="Loan Prediction API",
    version="1.0.0",
    description="Scores loan applications with a credit-risk model.",
    lifespan=lifespan,
)


class LoanApplication(BaseModel):
    income: float = Field(..., gt=0, description="Monthly income in USD", examples=[1200])
    loan_amount: float = Field(..., gt=0, description="Requested amount in USD", examples=[5000])
    term_months: int = Field(..., ge=1, le=120, description="Loan length in months", examples=[24])
    credit_score: int = Field(..., ge=300, le=850, examples=[680])
    employment_years: float = Field(..., ge=0, le=60, examples=[4])


class Prediction(BaseModel):
    score: float = Field(..., description="Probability of default, 0 = low risk, 1 = high risk")
    risk_band: str
    decision: str
    model_version: str


def risk_band(score: float) -> str:
    if score < 0.3:
        return "low"
    if score < 0.6:
        return "medium"
    return "high"


def save_prediction(application: LoanApplication, result: Prediction) -> None:
    if not DATABASE_URL:
        return
    import psycopg

    try:
        with psycopg.connect(DATABASE_URL, connect_timeout=3) as conn:
            conn.execute(
                """
                INSERT INTO predictions
                    (income, loan_amount, term_months, credit_score, employment_years,
                     score, risk_band, decision, model_version)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    application.income,
                    application.loan_amount,
                    application.term_months,
                    application.credit_score,
                    application.employment_years,
                    result.score,
                    result.risk_band,
                    result.decision,
                    result.model_version,
                ),
            )
    except psycopg.Error as exc:
        # Saving is best effort.
        logger.warning("Could not save prediction: %s", exc)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "model_loaded": "model" in state}


@app.post("/predict", response_model=Prediction)
def predict(application: LoanApplication) -> Prediction:
    bundle = state.get("model")
    if bundle is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    values = application.model_dump()
    row = np.array([[values[name] for name in bundle["features"]]], dtype=float)
    score = float(bundle["model"].predict_proba(row)[0][1])
    band = risk_band(score)
    result = Prediction(
        score=round(score, 4),
        risk_band=band,
        decision="reject" if band == "high" else "approve",
        model_version=bundle["version"],
    )
    save_prediction(application, result)
    return result

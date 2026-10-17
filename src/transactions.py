from pathlib import Path
import joblib
import numpy as np
import pandas as pd

REPO = Path(__file__).absolute().parent.parent
MODEL_PATH = REPO / "models" / "transaction_model.joblib"
HISTORY_PATH = REPO / "scenarios" / "history.csv"

RISKY_CATEGORIES = {"gift_card", "wire", "money_transfer"}
RISKY_REASON = "gift-card or wire payment"   # risk.py looks for this exact text

_model = None
_history = None

def _load():
    global _model, _history
    if _history is None:
        _history = pd.read_csv(HISTORY_PATH)
    if _model is None and MODEL_PATH.exists():
        _model = joblib.load(MODEL_PATH)

def _features(txn):
    amount = float(txn["amount"])
    past = _history[_history["user_id"] == txn["user_id"]]
    usual = past["amount"].median() if len(past) else 50.0
    return {
        "amount_ratio": min(amount / usual, 100.0) if usual > 0 else 1.0,
        "new_payee": int(txn.get("is_new_payee", 0)),
        "risky_category": int(str(txn.get("merchant_category", "")).lower() in RISKY_CATEGORIES),
        "hour": pd.Timestamp(txn["timestamp"]).hour,
    }

def _rule_score(f):
    s = 0.0
    if f["amount_ratio"] >= 5:   s += 0.4
    elif f["amount_ratio"] >= 3: s += 0.2
    if f["risky_category"]:      s += 0.3
    if f["new_payee"]:           s += 0.2
    if f["hour"] < 6 or f["hour"] >= 22: s += 0.1
    return min(s, 1.0)

def _model_score(f):
    if _model is None:
        return 0.0
    X = pd.DataFrame([f])[_model["features"]]
    a = -_model["model"].score_samples(X)[0]
    return float(np.clip((a - _model["p50"]) / (_model["p99"] - _model["p50"]), 0, 1))

def score_transaction(txn):
    _load()
    f = _features(txn)
    score = max(_model_score(f), _rule_score(f))
    reasons = []
    if f["amount_ratio"] >= 3:   reasons.append(f"{f['amount_ratio']:.0f}x usual amount")
    if f["risky_category"]:      reasons.append(RISKY_REASON)
    if f["new_payee"]:           reasons.append("new payee")
    if f["hour"] < 6 or f["hour"] >= 22: reasons.append("unusual hour")
    return {"score": round(score, 3), "reasons": reasons}

HOLD_THRESHOLD = 0.6        # tune in Phase 3
SAFETY_MSG_SCORE = 0.6      # scam-like message + gift card/wire = hold
RISKY_TXN_ALONE = 0.9       # very unusual gift card/wire = hold, even with no text
NORMAL_STORE_CAP = 0.45     # a big purchase at an ordinary store can't hold on its own
RULE_RISK = 0.85            # risk shown when a safety rule holds the payment
RISKY_REASON = "gift-card or wire payment"   # must match src/transactions.py

def decide(msg_result, txn_result):
    msg = float(msg_result["score"])
    txn = float(txn_result["score"])
    risky_payment = RISKY_REASON in txn_result["reasons"]

    txn_used = txn if risky_payment else min(txn, NORMAL_STORE_CAP)
    risk = 0.5 * msg + 0.5 * txn_used
    reasons = list(dict.fromkeys(msg_result["reasons"] + txn_result["reasons"]))

    safety_rule = risky_payment and (msg >= SAFETY_MSG_SCORE or txn >= RISKY_TXN_ALONE)
    if safety_rule:
        risk = max(risk, RULE_RISK)
        reasons.append("rule: risky payment channel")

    action = "hold_and_alert" if (safety_rule or risk >= HOLD_THRESHOLD) else "allow"
    return {"risk": round(risk, 3), "action": action, "reasons": reasons}

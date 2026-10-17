HOLD_THRESHOLD = 0.6      # tune this in Phase 3
SAFETY_MSG_SCORE = 0.6    # roadmap says 0.7; confirm with the team
RISKY_REASON = "gift-card or wire payment"   # backup only; must match src/transactions.py

def decide(msg_result, txn_result):
    msg = float(msg_result["score"])
    txn = float(txn_result["score"])
    risk = 0.5 * msg + 0.5 * txn

    # Is the payment a gift card / wire / money transfer?
    # Prefer the agreed key; fall back to the reason text if the Scorer hasn't added it yet.
    risky_payment = bool(txn_result.get("risky_category", False)) or RISKY_REASON in txn_result["reasons"]

    # Safety rule: scam-like message + gift card/wire payment = always hold
    safety_rule = msg >= SAFETY_MSG_SCORE and risky_payment
    if safety_rule:
        risk = max(risk, HOLD_THRESHOLD)

    action = "hold_and_alert" if risk >= HOLD_THRESHOLD else "allow"
    reasons = list(dict.fromkeys(msg_result["reasons"] + txn_result["reasons"]))
    if safety_rule:
        reasons.append("scam-like message just before a gift-card or wire payment")
    return {"risk": round(risk, 3), "action": action, "reasons": reasons}
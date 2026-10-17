# SafeCircle

**Real-time scam interception for older adults, running entirely on IBM LinuxONE.**
IBM Z Datathon 2026 · Theme: Real-Time AI for Critical Decisions

## The problem
Americans aged 60+ reported **$7.7 billion** in internet-crime losses in 2025 ([FBI/FTC via AARP](https://www.aarp.org/money/scams-fraud/fbi-ftc-report-2025-losses)).
Scams like the "grandparent scam" create urgency so money moves before anyone can step in.

## What SafeCircle does
At the moment a payment happens, SafeCircle checks two signals:

1. **Message model:** scores the recent text message for scam tactics (impersonating family, gift cards, secrecy, urgency).
2. **Transaction model:** scores whether the payment is unusual for that person (new payee, unusual amount, gift-card or wire merchant).
3. **Risk engine:** combines both. High risk → a short **cool-down hold** on the payment and an **alert to a trusted family member**.
4. **Explanation:** a plain-English, 2–3 sentence explanation for the senior. Personal details (names, phone numbers, card numbers, addresses) are **removed before** any text reaches a language model.

```
message ──► score_message() ──┐
                              ├──► decide() ──► hold + family alert
payment ──► score_transaction()┘        │
                                        └──► redact() ──► explain() ──► message to the senior
```

## Why IBM Z / LinuxONE
- Fraud checks must finish inside the payment-approval window. IBM Z runs AI next to the transaction data.
- The on-chip **Telum AI accelerator (NNPA)** is available to our models.
- **No data leaves the server:** models, messages, and the optional IBM Granite language model all run locally on LinuxONE. No external AI APIs.

## Results
| Component | Result |
|---|---|
| Message model (TF-IDF + Logistic Regression) | Precision 0.92, recall 0.94 on held-out test set |
| Transaction model | _TBD_ |
| Demo scenarios (Rosa, Walter, Linda) | 3 / 3 correct |
| Redaction | 45 test messages, 0 private details leaked |
| redact + explain speed | 0.047 ms per message (1,000 runs)|
| Optional Granite explanation | ~10 s per message, runs fully on-server |

## How to run
1. Open JupyterLab on the LinuxONE server.
2. Open `demo.ipynb` and choose **Kernel → Restart Kernel and Run All Cells**.
3. Each scenario prints the decision, the family alert (if held), and the explanation.

## Repository layout
```
src/messages.py       score_message()      - message scam model
src/transactions.py   score_transaction()  - unusual-payment model
src/risk.py           decide()             - risk engine + hold rule
src/explain.py        redact(), explain()  - privacy + plain-English explanation
scenarios/            demo scenarios (Rosa, Walter, Linda)
notebooks/            each pair's experiments
models/               trained model files
docs/screenshots/     evidence: LinuxONE platform, metrics, redaction
```

## Team
Miguel Jaimes · Akshi Biswal · Gabriel Aguilar-Vega · Aaron Nguyen

## Data and open-source credits
- [UCI SMS Spam Collection](https://archive.ics.uci.edu/dataset/228/sms+spam+collection): message training data
- IBM Z Datathon Lab 1 synthetic transaction data ([IBM TabFormer](https://github.com/IBM/TabFormer) family): transaction training data
- 42 hand-written scam and normal messages (our own, `data/extra_messages.csv`)
- [IBM Granite 4.0 (350M)](https://huggingface.co/ibm-granite): optional on-device explanations
- [llama.cpp](https://github.com/ggml-org/llama.cpp) / [llama-cpp-python](https://github.com/abetlen/llama-cpp-python): runs Granite on LinuxONE
- [scikit-learn](https://scikit-learn.org), [pandas](https://pandas.pydata.org), [joblib](https://joblib.readthedocs.io)
- [IBM LinuxONE Community Cloud](https://community.ibm.com/zsystems/l1cc/)
"""SafeCircle - redact() and explain()  (Message pair: Protector & Explainer)

redact()  : hides private details before any text reaches a language model.
explain() : plain-English explanation for the senior.
            Default = template (instant, always accurate, advice matched to the scam type).
            Optional = IBM Granite running locally on LinuxONE (use_granite=True),
            with an automatic quality check that falls back to the template.
"""
import re

# =========================== redact() ===========================

# Family words are the scam clue, not private data, so we never hide them
FAMILY_WORDS = {"Grandma", "Grandpa", "Grandmother", "Grandfather", "Nana", "Papa",
                "Mom", "Dad", "Mother", "Father", "Sir", "Madam", "Customer"}
# Titles are kept too ("Officer [NAME]"); only the name after them is hidden
TITLE_WORDS = {"Dr", "Mr", "Mrs", "Ms", "Officer", "Agent", "Deputy", "Sgt"}

# Names we know appear in our data
KNOWN_NAMES = ["Rosa", "Walter", "Linda"]

CARD_RE     = re.compile(r"\b\d(?:[ -]?\d){11,18}\b")                    # 12-19 digits
EMAIL_RE    = re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")             # name@site.com
LINK_RE     = re.compile(r"(?:https?://|www\.)\S+"
                         r"|\b[\w-]+(?:\.[\w-]+)*\.(?:com|net|org|xyz|info|io|co|us|ly)\b(?:/\S*)?")
PHONE_RE    = re.compile(r"(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\b\d{3}[-.\s]\d{4}\b")
ADDRESS_RE  = re.compile(r"\b\d{1,5}\s+(?:[A-Z][a-z]+\s+){1,3}(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Dr|Drive|Ln|Lane|Way|Ct|Court)\b")
TITLE_RE    = re.compile(r"\b((?:Dr|Mr|Mrs|Ms|Officer|Agent|Deputy|Sgt)\.?)\s+[A-Z][a-z]+")
GREETING_RE = re.compile(r"\b(Hi|Hello|Hey|Dear|this is|This is|it's|It's|it is|It is)\s+([A-Z][a-z]+)")


def redact(text: str) -> str:
    """Hide card numbers, emails, links, phones, addresses and names before text reaches the language model."""
    text = CARD_RE.sub("[CARD]", text)        # first, so the phone rule can't grab part of a card number
    text = EMAIL_RE.sub("[EMAIL]", text)      # before links, so an email isn't split up
    text = LINK_RE.sub("[LINK]", text)
    text = PHONE_RE.sub("[PHONE]", text)
    text = ADDRESS_RE.sub("[ADDRESS]", text)
    text = TITLE_RE.sub(r"\1 [NAME]", text)   # "Dr. Patel" -> "Dr. [NAME]"

    def hide_name(match):
        if match.group(2) in FAMILY_WORDS or match.group(2) in TITLE_WORDS:
            return match.group(0)             # keep "Hi Grandma" and "This is Officer"
        return f"{match.group(1)} [NAME]"     # "It's Tyler" -> "It's [NAME]"
    text = GREETING_RE.sub(hide_name, text)

    for name in KNOWN_NAMES:
        text = re.sub(rf"\b{name}\b", "[NAME]", text)
    return text


# =========================== explain() ===========================

# Message reasons start with a verb ("asks you to...", "claims to be...");
# payment reasons are short labels ("new payee", "gift-card merchant").
VERB_STARTS = ("asks", "claims", "says", "uses", "mentions", "pretends", "tells", "threatens", "offers", "promises")

# Whole-word matches only (so "mom" doesn't match "moment")
FAMILY_SCAM_RE = re.compile(r"\b(grandma|grandpa|grandmother|grandfather|grandson|granddaughter|grandchild|"
                            r"nana|papa|mom|dad|nephew|niece|family|relative)\b")
ACCOUNT_SCAM_RE = re.compile(r"\b(account|bank|identity|verify|password|pin)\b")


def _join(items):
    items = list(items)
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def _advice(msg_reasons, redacted_text=""):
    """Pick the safest next step for this type of scam, using the reasons AND the (redacted) message."""
    text = (" ".join(msg_reasons) + " " + redacted_text).lower()
    if FAMILY_SCAM_RE.search(text):
        return "Please call your family member at a number you already know before sending any money."
    if ACCOUNT_SCAM_RE.search(text):
        return ("Please call your bank using the number on the back of your card. "
                "Real banks never ask you to verify your identity by text.")
    return "Please call the person or company at a number you already know before sending any money."


def template_explain(decision: dict, redacted_text: str = "") -> str:
    """Explanation built only from the decision. No AI model, so it can never make things up."""
    if decision.get("action") != "hold_and_alert":
        return "This payment looks normal for you, so it went through. No action is needed."

    reasons = [r for r in decision.get("reasons", [])
               if not r.startswith("uses the word") and not r.startswith("rule:")]
    msg_reasons = [r for r in reasons if r.startswith(VERB_STARTS)][:3]
    pay_reasons = [r for r in reasons if not r.startswith(VERB_STARTS)][:3]

    parts = []
    if msg_reasons:
        parts.append(f"We paused this payment because the message {_join(msg_reasons)}.")
    else:
        parts.append("We paused this payment because it doesn't match your usual spending.")
    if pay_reasons:
        parts.append(f"The payment itself also looked unusual: {_join(pay_reasons)}.")
    parts.append("These are common signs of a scam, so we let your trusted contact know.")
    parts.append(_advice(msg_reasons, redacted_text))
    return " ".join(parts)


# ---- Optional: IBM Granite running locally on LinuxONE (nothing leaves the server) ----
GRANITE_PATH = "/home/ibm-user/granite-4.0-h-350m-base-be.f16.gguf"
_llm = None   # loaded the first time Granite is used, NOT when this file is imported

PAUSED_EXAMPLES = """Below are short, kind explanations for an older adult about why a payment was paused. Each uses simple words, 2 or 3 sentences, and never includes personal details.

Message: Hi Grandpa, it's [NAME]. I'm in jail and need $900 for bail. Please send it by Western Union and don't tell anyone.
Warning signs: claims to be a family member; asks for a money transfer; asks you to keep it secret
Explanation: We paused this payment because the message claims to be a family member, asks for money right away, and tells you to keep it secret. These are common signs of a scam. Please call your family member at a number you already know before sending anything.

Message: Your online store account is suspended. Confirm your card at [LINK] within 1 hour.
Warning signs: says your account has a problem; asks you to click a link; uses urgent language
Explanation: We paused this payment because the message says your account has a problem, pushes you to click a link, and rushes you. Real companies don't ask for card details this way. Please call the company using the number on your card or statement.
"""


def _get_llm():
    global _llm
    if _llm is None:
        from llama_cpp import Llama
        _llm = Llama(model_path=GRANITE_PATH, n_ctx=2048, n_threads=3, verbose=False)
    return _llm


def granite_explain(redacted_text: str, decision: dict) -> str:
    reasons = "; ".join(decision.get("reasons", []))
    prompt = PAUSED_EXAMPLES + f"\nMessage: {redacted_text}\nWarning signs: {reasons}\nExplanation:"
    out = _get_llm()(prompt, max_tokens=90, temperature=0, stop=["\n\n", "\nMessage:"])
    return out["choices"][0]["text"].strip()


def _looks_ok(text: str, decision: dict) -> bool:
    """Quality check on Granite's answer. If it fails, we use the template instead."""
    if not 40 <= len(text) <= 450:
        return False
    if not text.startswith("We paused"):
        return False
    if re.search(r"\d", text):                      # never show numbers the AI may have invented
        return False
    key_words = [" ".join(r.split()[:2]) for r in decision.get("reasons", [])]
    return any(k and k in text for k in key_words)  # must mention at least one real reason


def explain(redacted_text: str, decision: dict, use_granite: bool = False) -> str:
    """Return 2-3 plain-English sentences the senior can understand."""
    if decision.get("action") != "hold_and_alert" or not use_granite:
        return template_explain(decision, redacted_text)
    try:
        text = granite_explain(redacted_text, decision)
        if _looks_ok(text, decision):
            return text
    except Exception:
        pass                                        # any Granite problem -> safe template
    return template_explain(decision, redacted_text)
"""SafeCircle - redact() and explain()  (Message pair: Protector & Explainer)

redact()  : real version - hides private details before any text reaches the language model.
explain() : stub for now - real version (Granite or template) comes in P2-P4.
"""
import re

# Family words are the scam clue, not private data, so we never hide them
FAMILY_WORDS = {"Grandma", "Grandpa", "Grandmother", "Grandfather", "Nana", "Papa",
                "Mom", "Dad", "Mother", "Father", "Sir", "Madam", "Customer"}

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
        if match.group(2) in FAMILY_WORDS:
            return match.group(0)             # keep "Hi Grandma"
        return f"{match.group(1)} [NAME]"     # "It's Tyler" -> "It's [NAME]"
    text = GREETING_RE.sub(hide_name, text)

    for name in KNOWN_NAMES:
        text = re.sub(rf"\b{name}\b", "[NAME]", text)
    return text


def explain(redacted_text: str, decision: dict) -> str:
    """Return 2-3 plain-English sentences the senior can understand."""
    return "stub explanation - real version coming"
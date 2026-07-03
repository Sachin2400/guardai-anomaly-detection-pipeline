"""
Task 2.1: Named Entity Recognition
Task 2.2: Automated Masking Logic

Uses spaCy's en_core_web_sm (fast, CPU-friendly, ideal for a
demo/production service). Swap to `en_core_web_trf` (transformer-based,
more accurate) or HuggingFace `dslim/bert-base-NER` if you need
higher recall at the cost of latency.

Run once locally to download the model:
    python -m spacy download en_core_web_sm
"""

import re
import spacy
from functools import lru_cache

# Map spaCy entity labels -> the mask tag used in the API response
ENTITY_TAG_MAP = {
    "PERSON": "[PERSON]",
    "ORG": "[ORG]",
    "GPE": "[LOC]",     # cities/countries/states
    "LOC": "[LOC]",
    "FAC": "[LOC]",
}

# spaCy doesn't reliably tag emails/phones as entities -> regex safety net
EMAIL_RE = re.compile(r"[\w\.\-]+@[\w\-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"\b(?:\+?\d{1,3}[-\s]?)?\d{10}\b")


@lru_cache(maxsize=1)
def get_nlp():
    """Load the spaCy model once and cache it (expensive to load)."""
    return spacy.load("en_core_web_sm")


def extract_entities(text: str) -> list[dict]:
    """Returns list of {text, label, start, end} for recognized entities."""
    doc = get_nlp()(text)
    return [
        {"text": ent.text, "label": ent.label_, "start": ent.start_char, "end": ent.end_char}
        for ent in doc.ents
        if ent.label_ in ENTITY_TAG_MAP
    ]


def mask_pii(text: str) -> dict:
    """
    Replaces detected entities AND regex-matched emails/phones with
    generic tags. Returns the sanitized text plus what was masked
    (for audit logging — never log the raw original PII).
    """
    entities = extract_entities(text)

    # Merge NER spans with regex spans, sorted so we replace right-to-left
    # (keeps earlier character offsets valid as we mutate the string).
    spans = [(e["start"], e["end"], ENTITY_TAG_MAP[e["label"]]) for e in entities]
    for pattern, tag in [(EMAIL_RE, "[EMAIL]"), (PHONE_RE, "[PHONE]")]:
        for m in pattern.finditer(text):
            spans.append((m.start(), m.end(), tag))

    # Drop overlapping spans (keep the first / longest match)
    spans.sort(key=lambda s: (s[0], -(s[1] - s[0])))
    filtered = []
    last_end = -1
    for start, end, tag in spans:
        if start >= last_end:
            filtered.append((start, end, tag))
            last_end = end

    sanitized = text
    for start, end, tag in sorted(filtered, key=lambda s: s[0], reverse=True):
        sanitized = sanitized[:start] + tag + sanitized[end:]

    return {
        "sanitized_text": sanitized,
        "entities_found": [tag for _, _, tag in filtered],
        "entity_count": len(filtered),
    }


if __name__ == "__main__":
    sample = "My name is Alice Smith and my email is alice@example.com. I live in Patna."
    result = mask_pii(sample)
    print("Original :", sample)
    print("Sanitized:", result["sanitized_text"])
    print("Entities :", result["entities_found"])

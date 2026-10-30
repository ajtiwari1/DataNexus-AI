import re


PATTERNS = {
    "email": re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    ),
    "phone": re.compile(
        r"(?<!\d)(?:\+?\d{1,3}[- ]?)?[6-9]\d{9}(?!\d)"
    ),
}


def mask_pii(text: str) -> str:
    text = PATTERNS["email"].sub("[EMAIL_MASKED]", text)
    text = PATTERNS["phone"].sub("[PHONE_MASKED]", text)

    return text
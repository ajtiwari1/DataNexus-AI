import re
from dataclasses import dataclass


@dataclass
class InputCheck:
    allowed: bool
    reason: str | None = None
    risk_level: str = "low"


SUSPICIOUS_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"ignore\s+(all\s+)?system\s+prompts",
    r"reveal\s+(your\s+)?(system\s+prompt|hidden instructions)",
    r"show\s+(me\s+)?(your\s+)?(api key|secret|credentials)",
    r"developer\s+message",
    r"act\s+as\s+system",
]


def validate_user_input(question: str) -> InputCheck:
    normalized = question.lower()

    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, normalized):
            return InputCheck(
                allowed=False,
                reason="Potential prompt-injection attempt detected.",
                risk_level="high",
            )

    return InputCheck(allowed=True)
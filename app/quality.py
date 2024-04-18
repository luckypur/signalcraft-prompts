import re

FORBIDDEN = ["guaranteed resolved", "definitely fixed", "no customers affected", "100% secure"]


def score_draft(draft: str) -> dict:
    sections = {label: bool(re.search(rf"(?mi)^{re.escape(label)}:", draft))
                for label in ("Impact", "Action", "Next update")}
    issues = [f"Missing {label} section" for label, found in sections.items() if not found]
    issues.extend(f"Unsupported certainty: {phrase}" for phrase in FORBIDDEN if phrase in draft.lower())
    return {"score": round((3 - sum(not v for v in sections.values())) / 3 * 100),
            "passed": not issues, "issues": issues}

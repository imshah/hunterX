import re
from typing import Optional


def extract_sections(markdown: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current_header: Optional[str] = None
    current_lines: list[str] = []

    for line in markdown.splitlines():
        header_match = re.match(r"^#{1,3}\s+(.+)$", line)
        if header_match:
            if current_header is not None:
                sections[current_header] = "\n".join(current_lines).strip()
            current_header = header_match.group(1).strip().lower()
            current_lines = []
        elif current_header is not None:
            current_lines.append(line)

    if current_header is not None:
        sections[current_header] = "\n".join(current_lines).strip()

    return sections


def find_missing_sections(markdown: str) -> list[str]:
    sections = extract_sections(markdown)
    section_keys = set(sections.keys())

    required_groups = [
        (["summary", "objective", "professional summary"], "Summary/Objective"),
        (["experience", "work experience", "professional experience"], "Experience"),
        (["education"], "Education"),
        (["skills", "technical skills", "core competencies"], "Skills"),
    ]

    missing = []
    for variants, label in required_groups:
        if not any(v in section_keys for v in variants):
            missing.append(label)
    return missing


def count_quantified_bullets(markdown: str) -> tuple[int, int]:
    bullet_pattern = re.compile(r"^\s*[-*+]\s+(.+)$", re.MULTILINE)
    metric_pattern = re.compile(
        r"\d+[%+]|\$[\d,]+|\d+x\b|\d+\s*(users|customers|clients|projects|teams|employees|revenue|sales)",
        re.IGNORECASE,
    )

    bullets = bullet_pattern.findall(markdown)
    quantified = sum(1 for b in bullets if metric_pattern.search(b))
    return len(bullets), quantified


def estimate_pages(markdown: str, lines_per_page: int = 55) -> float:
    non_blank = [line for line in markdown.splitlines() if line.strip()]
    return len(non_blank) / lines_per_page

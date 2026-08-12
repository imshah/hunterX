from pathlib import Path
from unittest.mock import MagicMock

import pytest

from hunterx.models import ATSScore, DimensionScore, Job


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _dim(name: str, score: float, weight: float) -> DimensionScore:
    return DimensionScore(
        name=name,
        score=score,
        weight=weight,
        findings=[f"{name}: looks reasonable"],
        suggestions=[f"{name}: could improve"],
    )


@pytest.fixture
def sample_resume() -> str:
    return (FIXTURES_DIR / "sample_resume.md").read_text()


@pytest.fixture
def sample_jd() -> str:
    return (FIXTURES_DIR / "sample_jd.txt").read_text()


@pytest.fixture
def sample_job(sample_jd: str) -> Job:
    return Job(
        id="12345",
        title="Senior Backend Engineer",
        company="Acme Corp",
        description=sample_jd,
    )


@pytest.fixture
def sample_score() -> ATSScore:
    return ATSScore(
        keyword_coverage=_dim("Keyword Coverage", 75.0, 0.30),
        parsing_compliance=_dim("Parsing Compliance", 90.0, 0.25),
        section_completeness=_dim("Section Completeness", 85.0, 0.20),
        content_quality=_dim("Content Quality", 70.0, 0.15),
        timeline_consistency=_dim("Timeline Consistency", 95.0, 0.05),
        relevance_alignment=_dim("Relevance Alignment", 80.0, 0.05),
        overall_assessment="Good but needs keyword improvement.",
    )


@pytest.fixture
def high_score() -> ATSScore:
    return ATSScore(
        keyword_coverage=_dim("Keyword Coverage", 96.0, 0.30),
        parsing_compliance=_dim("Parsing Compliance", 98.0, 0.25),
        section_completeness=_dim("Section Completeness", 97.0, 0.20),
        content_quality=_dim("Content Quality", 95.0, 0.15),
        timeline_consistency=_dim("Timeline Consistency", 99.0, 0.05),
        relevance_alignment=_dim("Relevance Alignment", 94.0, 0.05),
        overall_assessment="Excellent ATS optimization.",
    )


@pytest.fixture
def mock_anthropic_client():
    client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [
        MagicMock(type="text", text="# Optimized Resume\n\n## Professional Summary\nTest")
    ]
    client.messages.create.return_value = mock_response
    return client

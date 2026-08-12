from hunterx.models import (
    ATSScore,
    DimensionScore,
    Job,
    OptimizationResult,
    OptimizationRound,
)


def test_dimension_weighted_score():
    dim = DimensionScore(
        name="Test", score=80.0, weight=0.30, findings=["f1"], suggestions=["s1"]
    )
    assert dim.weighted_score == 24.0


def test_ats_score_total(sample_score):
    expected = (
        75.0 * 0.30
        + 90.0 * 0.25
        + 85.0 * 0.20
        + 70.0 * 0.15
        + 95.0 * 0.05
        + 80.0 * 0.05
    )
    assert abs(sample_score.total_score - expected) < 0.01


def test_ats_score_failing_dimensions(sample_score):
    failing = sample_score.failing_dimensions
    names = [d.name for d in failing]
    assert "Keyword Coverage" in names
    assert "Content Quality" in names
    assert "Parsing Compliance" not in names


def test_ats_score_no_failing(high_score):
    assert len(high_score.failing_dimensions) == 0


def test_job_creation():
    job = Job(id="1", title="Eng", company="Co", description="desc")
    assert job.url is None


def test_job_defaults():
    job = Job(description="Some JD text")
    assert job.id == "manual"
    assert job.title == "(from file)"
    assert job.company == "(from file)"


def test_optimization_round_serialization(sample_score):
    r = OptimizationRound(
        round_number=1, resume_markdown="# Test", score=sample_score
    )
    data = r.model_dump()
    assert data["round_number"] == 1
    assert data["feedback"] is None


def test_optimization_result(sample_score, sample_job):
    r = OptimizationRound(
        round_number=1, resume_markdown="# Optimized", score=sample_score
    )
    result = OptimizationResult(
        original_resume="# Original",
        optimized_resume="# Optimized",
        job=sample_job,
        rounds=[r],
        final_score=sample_score,
    )
    assert result.optimized_resume == "# Optimized"
    assert len(result.rounds) == 1

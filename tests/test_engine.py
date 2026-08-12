from unittest.mock import MagicMock, patch

import pytest

from hunterx.config import Settings
from hunterx.models import ATSScore, DimensionScore, OptimizationRound


def _make_score(total_approx: float) -> ATSScore:
    base = min(total_approx, 100.0)
    return ATSScore(
        keyword_coverage=DimensionScore(
            name="Keyword Coverage", score=base, weight=0.30,
            findings=["ok"], suggestions=["improve"],
        ),
        parsing_compliance=DimensionScore(
            name="Parsing Compliance", score=min(base + 5, 100.0), weight=0.25,
            findings=["ok"], suggestions=["improve"],
        ),
        section_completeness=DimensionScore(
            name="Section Completeness", score=min(base + 3, 100.0), weight=0.20,
            findings=["ok"], suggestions=["improve"],
        ),
        content_quality=DimensionScore(
            name="Content Quality", score=base, weight=0.15,
            findings=["ok"], suggestions=["improve"],
        ),
        timeline_consistency=DimensionScore(
            name="Timeline Consistency", score=min(base + 4, 100.0), weight=0.05,
            findings=["ok"], suggestions=["improve"],
        ),
        relevance_alignment=DimensionScore(
            name="Relevance Alignment", score=min(base + 2, 100.0), weight=0.05,
            findings=["ok"], suggestions=["improve"],
        ),
        overall_assessment="Test assessment.",
    )


@pytest.fixture
def settings(monkeypatch):
    monkeypatch.setenv("KIMI_API_TOKEN", "sk-test-token")
    return Settings(optimization_rounds=5, target_score=95)


def _text_block(text: str) -> MagicMock:
    return MagicMock(type="text", text=text)


def _mock_create_client():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [_text_block("# Round N resume")]
    mock_client.messages.create.return_value = mock_response
    return mock_client


def test_engine_runs_all_rounds(settings, sample_job, sample_resume):
    with patch("hunterx.config.Settings.create_llm_client", return_value=_mock_create_client()), \
         patch("hunterx.optimizer.engine.ATSScorer") as MockScorer, \
         patch("hunterx.optimizer.engine.Critic") as MockCritic:

        scores = [_make_score(70), _make_score(75), _make_score(80), _make_score(85), _make_score(88)]
        MockScorer.return_value.score.side_effect = scores
        MockCritic.return_value.generate_feedback.return_value = "Add more keywords"

        from hunterx.optimizer.engine import OptimizationEngine

        rounds_seen = []
        engine = OptimizationEngine(
            settings, on_round_complete=lambda r: rounds_seen.append(r)
        )
        result = engine.optimize(sample_resume, sample_job)

        assert len(result.rounds) == 5
        assert len(rounds_seen) == 5
        assert result.final_score.total_score == max(
            r.score.total_score for r in result.rounds
        )


def test_engine_early_termination(settings, sample_job, sample_resume):
    with patch("hunterx.config.Settings.create_llm_client", return_value=_mock_create_client()), \
         patch("hunterx.optimizer.engine.ATSScorer") as MockScorer, \
         patch("hunterx.optimizer.engine.Critic") as MockCritic:

        MockScorer.return_value.score.return_value = _make_score(96)

        from hunterx.optimizer.engine import OptimizationEngine

        engine = OptimizationEngine(settings)
        result = engine.optimize(sample_resume, sample_job)

        assert len(result.rounds) == 1
        MockCritic.return_value.generate_feedback.assert_not_called()


def test_engine_selects_best_round(settings, sample_job, sample_resume):
    mock_client = _mock_create_client()
    resumes = ["# Round 1", "# Round 2 best", "# Round 3", "# Round 4", "# Round 5"]
    mock_client.messages.create.side_effect = [
        MagicMock(content=[_text_block(r)]) for r in resumes
    ]

    with patch("hunterx.config.Settings.create_llm_client", return_value=mock_client), \
         patch("hunterx.optimizer.engine.ATSScorer") as MockScorer, \
         patch("hunterx.optimizer.engine.Critic") as MockCritic:

        scores = [_make_score(75), _make_score(92), _make_score(85), _make_score(88), _make_score(80)]
        MockScorer.return_value.score.side_effect = scores
        MockCritic.return_value.generate_feedback.return_value = "feedback"

        from hunterx.optimizer.engine import OptimizationEngine

        engine = OptimizationEngine(settings)
        result = engine.optimize(sample_resume, sample_job)

        assert result.optimized_resume == "# Round 2 best"

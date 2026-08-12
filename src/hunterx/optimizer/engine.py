import logging
from typing import Callable, Optional

from hunterx.config import Settings
from hunterx.models import ATSScore, Job, OptimizationResult, OptimizationRound
from hunterx.optimizer import first_text
from hunterx.optimizer.critic import Critic
from hunterx.optimizer.prompts import COVER_LETTER_PROMPT, INITIAL_OPTIMIZATION_PROMPT, REFINEMENT_PROMPT
from hunterx.optimizer.scorer import ATSScorer

logger = logging.getLogger(__name__)


class OptimizationEngine:
    def __init__(
        self,
        settings: Settings,
        on_round_complete: Optional[Callable[[OptimizationRound], None]] = None,
    ) -> None:
        self._client = settings.create_llm_client()
        self._model = settings.kimi_model
        self._thinking = settings.thinking_param
        self._scorer = ATSScorer(settings)
        self._critic = Critic(settings)
        self._max_rounds = settings.optimization_rounds
        self._target_score = settings.target_score
        self._on_round_complete = on_round_complete

    def optimize(self, base_resume: str, job: Job) -> OptimizationResult:
        rounds: list[OptimizationRound] = []
        current_resume = base_resume

        for round_num in range(1, self._max_rounds + 1):
            logger.info(f"Starting optimization round {round_num}/{self._max_rounds}")

            if round_num == 1:
                current_resume = self._generate_initial(base_resume, job.description)
            else:
                prev_round = rounds[-1]
                current_resume = self._refine(
                    current_resume=current_resume,
                    job_description=job.description,
                    score=prev_round.score,
                    feedback=prev_round.feedback or "",
                    round_number=round_num,
                )

            score = self._scorer.score(current_resume, job.description)
            logger.info(f"Round {round_num} score: {score.total_score:.1f}")

            should_continue = (
                score.total_score < self._target_score
                or len(score.failing_dimensions) > 0
            )

            feedback: Optional[str] = None
            if should_continue and round_num < self._max_rounds:
                feedback = self._critic.generate_feedback(
                    current_resume, job.description, score
                )

            optimization_round = OptimizationRound(
                round_number=round_num,
                resume_markdown=current_resume,
                score=score,
                feedback=feedback,
            )
            rounds.append(optimization_round)

            if self._on_round_complete:
                self._on_round_complete(optimization_round)

            if not should_continue:
                logger.info(f"Target score reached at round {round_num}")
                break

        best_round = max(rounds, key=lambda r: r.score.total_score)

        return OptimizationResult(
            original_resume=base_resume,
            optimized_resume=best_round.resume_markdown,
            job=job,
            rounds=rounds,
            final_score=best_round.score,
        )

    def generate_cover_letter(self, resume: str, job_description: str) -> str:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=2048,
            thinking=self._thinking,
            messages=[
                {
                    "role": "user",
                    "content": COVER_LETTER_PROMPT.format(
                        resume=resume,
                        job_description=job_description,
                    ),
                }
            ],
        )
        return first_text(response)

    def _generate_initial(self, base_resume: str, job_description: str) -> str:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=8192,
            thinking=self._thinking,
            messages=[
                {
                    "role": "user",
                    "content": INITIAL_OPTIMIZATION_PROMPT.format(
                        base_resume=base_resume,
                        job_description=job_description,
                    ),
                }
            ],
        )
        return first_text(response)

    def _refine(
        self,
        current_resume: str,
        job_description: str,
        score: ATSScore,
        feedback: str,
        round_number: int,
    ) -> str:
        dimension_scores = "\n".join(
            f"- {d.name}: {d.score}/100 (weighted: {d.weighted_score:.1f})"
            for d in score.dimensions
        )

        response = self._client.messages.create(
            model=self._model,
            max_tokens=8192,
            thinking=self._thinking,
            messages=[
                {
                    "role": "user",
                    "content": REFINEMENT_PROMPT.format(
                        round_number=round_number,
                        job_description=job_description,
                        current_resume=current_resume,
                        total_score=score.total_score,
                        dimension_scores=dimension_scores,
                        feedback=feedback,
                    ),
                }
            ],
        )
        return first_text(response)

from hunterx.config import Settings
from hunterx.models import ATSScore
from hunterx.optimizer import first_text
from hunterx.optimizer.prompts import CRITIQUE_PROMPT


class Critic:
    def __init__(self, settings: Settings) -> None:
        self._client = settings.create_llm_client()
        self._model = settings.kimi_model
        self._thinking = settings.thinking_param

    def generate_feedback(
        self, resume: str, job_description: str, score: ATSScore
    ) -> str:
        dimension_details = self._format_dimensions(score)

        response = self._client.messages.create(
            model=self._model,
            max_tokens=2048,
            thinking=self._thinking,
            messages=[
                {
                    "role": "user",
                    "content": CRITIQUE_PROMPT.format(
                        job_description=job_description,
                        resume=resume,
                        total_score=score.total_score,
                        dimension_details=dimension_details,
                    ),
                }
            ],
        )
        return first_text(response)

    def _format_dimensions(self, score: ATSScore) -> str:
        lines = []
        for dim in score.dimensions:
            lines.append(f"### {dim.name}: {dim.score}/100 (weight: {dim.weight})")
            lines.append(f"Findings: {'; '.join(dim.findings)}")
            lines.append(f"Suggestions: {'; '.join(dim.suggestions)}")
            lines.append("")
        return "\n".join(lines)

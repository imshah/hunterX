import json

from hunterx.config import Settings
from hunterx.models import ATSScore
from hunterx.optimizer.prompts import (
    EVAL_SYSTEM_PROMPT,
    EVAL_USER_PROMPT,
    SCORING_SYSTEM_PROMPT,
    SCORING_USER_PROMPT,
)

SCORE_TOOL = {
    "name": "submit_ats_score",
    "description": "Submit the ATS score breakdown for the resume evaluation.",
    "input_schema": ATSScore.model_json_schema(),
}


class ATSScorer:
    def __init__(self, settings: Settings) -> None:
        self._client = settings.create_llm_client()
        self._model = settings.kimi_model
        self._thinking = settings.thinking_param

    def score(self, resume: str, job_description: str) -> ATSScore:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=4096,
            thinking=self._thinking,
            system=SCORING_SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": SCORING_USER_PROMPT.format(
                        job_description=job_description,
                        resume=resume,
                    ),
                }
            ],
            tools=[SCORE_TOOL],
            tool_choice={"type": "tool", "name": "submit_ats_score"},
        )

        for block in response.content:
            if block.type == "tool_use" and block.name == "submit_ats_score":
                return ATSScore.model_validate(block.input)

        raise ValueError("Model did not return a tool_use block with ATS score")

    def evaluate(self, resume: str) -> ATSScore:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=4096,
            thinking=self._thinking,
            system=EVAL_SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": EVAL_USER_PROMPT.format(resume=resume),
                }
            ],
            tools=[SCORE_TOOL],
            tool_choice={"type": "tool", "name": "submit_ats_score"},
        )

        for block in response.content:
            if block.type == "tool_use" and block.name == "submit_ats_score":
                return ATSScore.model_validate(block.input)

        raise ValueError("Model did not return a tool_use block with ATS score")

from typing import Optional

from pydantic import BaseModel, Field


class Job(BaseModel):
    id: str = Field(default="manual")
    title: str = Field(default="(from file)")
    company: str = Field(default="(from file)")
    description: str = Field(description="Full job description text")
    url: Optional[str] = None


class DimensionScore(BaseModel):
    name: str
    score: float = Field(ge=0.0, le=100.0)
    weight: float
    findings: list[str] = Field(description="Specific observations for this dimension")
    suggestions: list[str] = Field(description="Specific improvements for this dimension")

    @property
    def weighted_score(self) -> float:
        return self.score * self.weight


class ATSScore(BaseModel):
    keyword_coverage: DimensionScore
    parsing_compliance: DimensionScore
    section_completeness: DimensionScore
    content_quality: DimensionScore
    timeline_consistency: DimensionScore
    relevance_alignment: DimensionScore
    overall_assessment: str = Field(description="1-2 sentence summary")

    @property
    def dimensions(self) -> list[DimensionScore]:
        return [
            self.keyword_coverage,
            self.parsing_compliance,
            self.section_completeness,
            self.content_quality,
            self.timeline_consistency,
            self.relevance_alignment,
        ]

    @property
    def total_score(self) -> float:
        return sum(d.weighted_score for d in self.dimensions)

    @property
    def failing_dimensions(self) -> list[DimensionScore]:
        return [d for d in self.dimensions if d.score < 80.0]


class OptimizationRound(BaseModel):
    round_number: int
    resume_markdown: str
    score: ATSScore
    feedback: Optional[str] = None


class OptimizationResult(BaseModel):
    original_resume: str
    optimized_resume: str
    job: Job
    rounds: list[OptimizationRound]
    final_score: ATSScore

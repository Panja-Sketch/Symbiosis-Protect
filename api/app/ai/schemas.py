from typing import Literal

from pydantic import BaseModel, Field


class ModelAnswer(BaseModel):
    """The enforced output schema (BUILD_SPEC section 8). Gemini must return exactly this."""

    answer_plain: str = Field(max_length=1800)
    cited_coverage_codes: list[str] = Field(default_factory=list)
    confidence: Literal["high", "medium", "low"]
    needs_agent: bool
    suggested_actions: list[str] = Field(default_factory=list, max_length=4)


class GroundedAnswer(ModelAnswer):
    cited_glossary_terms: list[str] = Field(default_factory=list)
    source: Literal["gemini", "template"] = "template"
    provenance: Literal["AI", "SYNTHETIC"] = "SYNTHETIC"  # AI only when Gemini phrased the answer
    fallback_reason: str | None = None
    disclaimer: str = "Based only on your policy summary. Your agent confirms final coverage decisions."


class PolicyContext(BaseModel):
    """Everything the assistant is allowed to know. No web access, no other accounts."""

    lob: str
    product_label: str
    coverages: list[dict]
    endorsements: list[dict]
    exclusions_plain: list[dict]
    deductibles: dict
    coverage_notes: list[dict]
    glossary: list[dict]
    open_tasks: list[dict]
    agent: dict

    def codes(self) -> set[str]:
        return ({c["code"] for c in self.coverages} | {e["code"] for e in self.endorsements}
                | {x["code"] for x in self.exclusions_plain})

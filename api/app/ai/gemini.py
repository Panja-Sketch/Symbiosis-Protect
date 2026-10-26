"""GeminiExplainer: Vertex AI via google-genai, service-account auth (no API key). Grounded on PolicyContext only."""

import json

from app.ai.schemas import GroundedAnswer, ModelAnswer, PolicyContext

SYSTEM = """You answer a policyholder's question about THEIR insurance policy summary.
Rules, all mandatory:
1. Use ONLY the JSON policy data provided. If the answer is not in it, say you could not find it and set needs_agent=true.
2. Never state that a specific loss WILL be covered or paid. Use phrases like "your policy summary says..." and "your agent confirms final coverage decisions".
3. No legal, pricing or claim-decision advice. Suggest add-ons only as "ask your agent about...".
4. Every coverage, endorsement or exclusion you rely on must have its code in cited_coverage_codes (codes exactly as given).
5. Quote dollar amounts only if they appear in the cited items.
6. Plain language, at most 6 sentences. Output JSON matching the schema, nothing else."""


class GeminiExplainer:
    name = "gemini"

    def __init__(self, project: str, location: str, model: str, client=None):
        self.model = model
        if client is None:
            from google import genai

            client = genai.Client(vertexai=True, project=project, location=location)
        self.client = client

    def _contents(self, question: str, ctx: PolicyContext) -> str:
        data = ctx.model_dump()
        return f"POLICY DATA:\n{json.dumps(data, default=str)}\n\nQUESTION:\n{question}"

    def answer(self, question: str, ctx: PolicyContext) -> GroundedAnswer:
        from google.genai import types

        resp = self.client.models.generate_content(
            model=self.model, contents=self._contents(question, ctx),
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM, response_mime_type="application/json", response_schema=ModelAnswer,
                max_output_tokens=500, temperature=0.2))
        parsed = ModelAnswer.model_validate_json(resp.text)
        return GroundedAnswer(**parsed.model_dump(), source="gemini", provenance="AI")

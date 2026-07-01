from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from app.config import settings
from app.schemas.requirement import StructuredRequirement
from app.schemas.testcase import TestCase

PARSE_SYSTEM_PROMPT = """You are an automotive test requirement analyst.
Your ONLY task: read the user-provided requirement and convert it into structured JSON.
Do NOT invent additional test logic or infer conditions not stated in the requirement.
- feature: name of the related function/feature
- trigger: activation condition (combine all triggering conditions from the requirement)
- vehicle_status: relevant vehicle state (e.g. moving, stationary, door open...)
- domain: a short word/phrase for the automotive functional domain (e.g. Body Control, ADAS, Powertrain, Climate Control)
- description: one concise summary sentence that normalizes the requirement (preserve original meaning)
"""

REFINE_SYSTEM_PROMPT = """You are an automotive test case editor.
Your ONLY task: rewrite the action/expected_result fields of each step and the title/final_expected_result to be clear and grammatically correct English.

Rules for action field:
- Write each action as a direct, concrete instruction starting with a verb (e.g. "Touch", "Set", "Press", "Turn", "Verify").
- Be specific: include exact values, signal names, button names, or thresholds from the Technical Reference when available.
- Do NOT start with "Step N:" — the step number is already tracked in step_number.
- Example good action: "Press the front defrost button on the central control panel."
- Example good action: "Set fan speed from 0 to level 3 using the virtual button."

Rules for expected_result field:
- State the observable outcome precisely (what is displayed, what signal changes, what actuator activates).
- Use exact CAN signal names, threshold values, or mode names from the Technical Reference when available.
- Example: "The MHU displays fan speed = 3 and wind output is audible."

STRICTLY FORBIDDEN: adding/removing/reordering steps, adding/removing preconditions, changing testcase_id/domain/
derived_from_testcase_id/coverage_classification/coverage_score/generation_path/source_requirement.
Keep the same number of steps and step_number values as the input.
All output text must be in English.
"""

DECOMPOSE_SYSTEM_PROMPT = """You are an expert test requirement analyst for automotive control systems (CCU/BCM/ADAS/Climate Control).
Task: read the overall requirement and decompose it into 3-5 INDEPENDENT, concrete, immediately testable test scenarios.
Each scenario describes EXACTLY ONE activation condition + ONE expected outcome.
Mandatory rules:
- Preserve original technical parameters (signal names, threshold values, units)
- Each scenario must be self-contained (runnable without other scenarios)
- Must cover: the main happy path, independent sub-functions, default/boundary states
- Do NOT create duplicate scenarios or combine multiple functions into one scenario
Return only JSON: {{"scenarios": ["<scenario 1 description in English>", "<scenario 2>", ...]}}
"""


class _ScenariosOutput(BaseModel):
    scenarios: list[str]


class GeminiClient:
    def __init__(self) -> None:
        self._chat = ChatGoogleGenerativeAI(
            model=settings.gemini_chat_model,
            google_api_key=settings.google_api_key,
            temperature=0.2,
        )
        self._embeddings = GoogleGenerativeAIEmbeddings(
            model=settings.gemini_embedding_model,
            google_api_key=settings.google_api_key,
        )

    def parse_to_structured(self, raw_text: str) -> StructuredRequirement:
        structured_llm = self._chat.with_structured_output(StructuredRequirement)
        result = structured_llm.invoke(
            [
                ("system", PARSE_SYSTEM_PROMPT),
                ("human", raw_text),
            ]
        )
        result.raw_text = raw_text
        return result

    def refine_wording(
        self,
        draft_testcase: TestCase,
        structured_requirement: StructuredRequirement,
        bcm_context: list[str] | None = None,
    ) -> TestCase:
        structured_llm = self._chat.with_structured_output(TestCase)

        bcm_section = ""
        if bcm_context:
            joined = "\n\n---\n\n".join(bcm_context)
            bcm_section = f"\n\n=== Technical Reference (BCM/Spec) ===\n{joined}\n=== End Technical Reference ==="

        prompt = (
            f"Original requirement: {structured_requirement.raw_text}"
            f"{bcm_section}\n\n"
            f"Test case to rewrite in clear English (preserve structure):\n"
            f"{draft_testcase.model_dump_json(indent=2)}"
        )
        return structured_llm.invoke(
            [
                ("system", REFINE_SYSTEM_PROMPT),
                ("human", prompt),
            ]
        )

    def decompose_to_scenarios(self, requirement: str) -> list[str]:
        structured_llm = self._chat.with_structured_output(_ScenariosOutput)
        try:
            result = structured_llm.invoke(
                [
                    ("system", DECOMPOSE_SYSTEM_PROMPT),
                    ("human", requirement),
                ]
            )
            scenarios = [s.strip() for s in result.scenarios if s.strip()]
            return scenarios if scenarios else [requirement]
        except Exception:
            return [requirement]

    def embed(self, text: str) -> list[float]:
        return self._embeddings.embed_query(text)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return self._embeddings.embed_documents(texts)

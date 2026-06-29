from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from app.config import settings
from app.schemas.requirement import StructuredRequirement
from app.schemas.testcase import TestCase

PARSE_SYSTEM_PROMPT = """Ban la mot bo phan tich requirement kiem thu o to.
Nhiem vu DUY NHAT: doc requirement tu do nguoi dung nhap va chuyen thanh JSON co cau truc.
KHONG tu sinh them logic test, KHONG suy dien dieu kien khong co trong requirement.
- feature: ten chuc nang lien quan
- trigger: dieu kien kich hoat (gop tat ca dieu kien dieu kien trong requirement)
- vehicle_status: trang thai xe lien quan (vi du: dang chay, dung yen, cua mo...)
- domain: mot tu/cum tu ngan chi mien chuc nang o to (vi du: Body Control, ADAS, Powertrain, Infotainment)
- description: 1 cau tom tat ngan gon, chuan hoa lai requirement (giu nguyen y nghia)
"""

REFINE_SYSTEM_PROMPT = """Ban la bien tap vien testcase kiem thu o to.
Nhiem vu DUY NHAT: viet lai cho ro rang, dung ngu phap cac truong action/expected_result cua tung step,
va title/final_expected_result.
TUYET DOI KHONG duoc: them/xoa/doi thu tu step, them/xoa precondition, doi testcase_id/domain/
derived_from_testcase_id/coverage_classification/coverage_score/generation_path/source_requirement.
Giu nguyen so luong step va step_number nhu input.
"""


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

    def refine_wording(self, draft_testcase: TestCase, structured_requirement: StructuredRequirement) -> TestCase:
        structured_llm = self._chat.with_structured_output(TestCase)
        prompt = (
            f"Requirement goc: {structured_requirement.raw_text}\n\n"
            f"Testcase can vie lai cho ro rang hon (giu nguyen cau truc):\n"
            f"{draft_testcase.model_dump_json(indent=2)}"
        )
        return structured_llm.invoke(
            [
                ("system", REFINE_SYSTEM_PROMPT),
                ("human", prompt),
            ]
        )

    def embed(self, text: str) -> list[float]:
        return self._embeddings.embed_query(text)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return self._embeddings.embed_documents(texts)

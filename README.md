# Automotive Test Case Generator

Hệ thống sinh test case ô tô từ requirement tự nhiên, kết hợp RAG (testcase cũ trong Qdrant), Coverage Engine + Gap Detector, Rule Engine theo domain, và Gemini (chỉ dùng để parse requirement và viết lại câu chữ — không sinh logic test).

## Kiến trúc

```
Requirement (text) -> parse_requirement (Gemini) -> embed_requirement -> retrieve_candidates (Qdrant)
  -> score_coverage (Coverage Engine + Gap Detector)
      > 90%        -> reuse_high_match     (lấy testcase cũ, chỉ patch điều kiện thiếu)
      50% - 90%     -> merge_partial_match  (base RAG + delta từ Rule Engine, merge)
      < 50%         -> generate_from_rules  (chỉ Rule Engine sinh skeleton theo domain)
  -> llm_refine (Gemini chỉ viết lại câu chữ, validate giữ nguyên cấu trúc)
  -> finalize_output -> Test Case hoàn chỉnh
```

Công thức coverage score: `combined_score = round(100 * (0.6 * cosine_similarity + 0.4 * field_match_score))`, với `field_match_score` là trung bình có trọng số giữa domain/feature/trigger/vehicle_status.

## Cấu trúc thư mục

```
app/
  main.py              # FastAPI app
  config.py            # Settings đọc từ .env
  api/                 # routes.py, dependencies.py
  schemas/             # StructuredRequirement, TestCase, CoverageScoreResult, PipelineState
  clients/             # GeminiClient, QdrantClientWrapper
  graph/               # LangGraph builder, routing, nodes/
  rule_engine/         # base.py, registry.py, domains/ (body_control, adas, powertrain, _generic)
  ingestion/           # excel_loader, build_payload, ingest.py (CLI)
  utils/                # similarity.py (coverage scoring), text_rules.py
config/
  column_mapping.yaml  # mapping cột Excel thật -> field chuẩn (sửa file này khi đổi cấu trúc Excel)
scripts/run_ingestion.py
tests/
```

## 1. Cài đặt

```bash
cd c:\Users\tminh\Workspace\dev_AI_automation
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Cấu hình `.env`

```bash
copy .env.example .env
```

Điền vào `.env`:

```
GOOGLE_API_KEY=<gemini api key>
QDRANT_URL=<url cluster Qdrant Cloud>
QDRANT_API_KEY=<api key Qdrant Cloud>
QDRANT_COLLECTION_NAME=historical_testcases
GEMINI_CHAT_MODEL=gemini-2.0-flash
GEMINI_EMBEDDING_MODEL=models/text-embedding-004
EMBEDDING_DIM=768
```

## 3. Chạy test

Không cần API key (chỉ test schema, rule engine, coverage scoring, routing — thuần Python):

```bash
pytest tests/ -v
```

## 4. Ingest testcase cũ (Excel) vào Qdrant

1. Đặt file Excel vào `data/` (ví dụ `data/historical_testcases.xlsx`).
2. Sửa `config/column_mapping.yaml`, đổi giá trị bên phải mỗi dòng trong `columns:` khớp với tên cột thật trong file Excel của bạn (KHÔNG cần sửa code).
3. Chạy:

```bash
python scripts/run_ingestion.py data/historical_testcases.xlsx
```

Script sẽ tự tạo collection trên Qdrant (nếu chưa có), embed từng dòng bằng Gemini, và upsert vào Qdrant (idempotent — chạy lại không tạo trùng).

## 5. Chạy server

```bash
uvicorn app.main:app --reload
```

Server chạy tại `http://127.0.0.1:8000`, Swagger UI tại `http://127.0.0.1:8000/docs`.

## 6. Gọi thử API

Kiểm tra health (kiểm tra luôn kết nối Qdrant):

```bash
curl http://127.0.0.1:8000/health
```

Sinh test case từ requirement:

```bash
curl -X POST http://127.0.0.1:8000/testcases/generate ^
  -H "Content-Type: application/json" ^
  -d "{\"requirement_text\": \"Khi toc do xe vuot 30km/h va cua xe dang mo, he thong phai keu chuong canh bao\"}"
```

Response trả về `testcase` (test case hoàn chỉnh) và `coverage` (điểm số + testcase cũ gần nhất nếu có, để truy vết).

## Thêm domain mới cho Rule Engine

Copy `app/rule_engine/domains/_template.py` sang file mới (tên không bắt đầu bằng `_`, ví dụ `infotainment.py`), implement `generate_skeleton()`. `registry.py` tự động quét và đăng ký domain mới — không cần sửa code engine.

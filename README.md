# Automotive Test Case Generator

Tự động sinh test case ô tô từ requirement, kết hợp:
- **RAG** — tìm testcase cũ tương tự trong Qdrant
- **Coverage Engine** — chấm điểm độ phủ (cosine similarity + field match)
- **Rule Engine** — sinh skeleton theo domain (Body Control, ADAS, Climate Control, Powertrain...)
- **Gemini** — chỉ dùng để: decompose requirement → scenarios, parse requirement → structured JSON, và viết lại câu chữ tiếng Anh (không sinh logic test)

## Pipeline

```
Requirement (text)
  └─► decompose_to_scenarios (Gemini) ──► [scenario 1, scenario 2, ...]
                                              │  (chạy song song)
                                              ▼
                            parse_requirement (Gemini)
                                              │
                                              ▼
                            embed_requirement (Gemini Embeddings)
                                              │
                                              ▼
                            retrieve_candidates (Qdrant top-k)
                                              │
                                              ▼
                            score_coverage (cosine + field match)
                              │          │          │
                           > 90%      50–90%      < 50%
                              │          │          │
                        reuse_high  merge_partial  generate
                         _match      _match       _from_rules
                              └──────────┴──────────┘
                                              │
                                              ▼
                            llm_refine (Gemini — viết lại câu chữ)
                                              │
                                              ▼
                            finalize_output → TestCase hoàn chỉnh
```

**Coverage score:** `100 × (0.6 × cosine_similarity + 0.4 × field_match_score)`  
**Classification:** `> 90` → High Match | `50–90` → Partial Match | `< 50` → New

## Cấu trúc thư mục

```
app/
  main.py                  # FastAPI app + lifespan
  config.py                # Settings đọc từ .env
  api/
    routes.py              # POST /testcases/generate, /testcases/generate/export, GET /health
    dependencies.py
  schemas/                 # StructuredRequirement, TestCase, CoverageScoreResult, PipelineState
  clients/
    gemini_client.py       # GeminiClient (parse, decompose, refine, embed)
    qdrant_client.py       # QdrantClientWrapper
  graph/
    builder.py             # LangGraph build_graph()
    routing.py             # route_by_coverage
    nodes/                 # parse, embed, retrieve, score, reuse, merge, generate, refine, finalize
  rule_engine/
    base.py                # DomainRuleSet ABC
    registry.py            # Auto-scan & register domains
    domains/               # body_control.py, adas.py, powertrain.py, _generic.py, _template.py
  ingestion/
    excel_loader.py
    build_payload.py
    column_mapping.py
    ingest.py
  utils/
    similarity.py          # coverage scoring & classification
    excel_exporter.py      # build_excel() → bytes
config/
  column_mapping.yaml        # mapping cho VF34_update.xlsx
  minio_column_mapping.yaml  # mapping cho Minio.xlsx
outputs/                     # file Excel kết quả tự động lưu tại đây
scripts/
  run_ingestion.py
tests/
```

---

## 1. Cài đặt

```bash
# Clone project
cd dev_AI_automation

# Tạo virtual environment
python -m venv .venv

# Kích hoạt (Windows)
.venv\Scripts\activate
# Kích hoạt (Mac/Linux)
source .venv/bin/activate

# Cài dependencies
pip install -r requirements.txt
```

---

## 2. Cấu hình `.env`

Tạo file `.env` ở thư mục gốc:

```env
GOOGLE_API_KEY=<Gemini API key của bạn>
QDRANT_URL=<URL Qdrant Cloud cluster>
QDRANT_API_KEY=<Qdrant API key>
QDRANT_COLLECTION_NAME=historical_testcases
GEMINI_CHAT_MODEL=gemini-2.5-flash
GEMINI_EMBEDDING_MODEL=models/gemini-embedding-001
EMBEDDING_DIM=3072
```

> Lấy Gemini API key tại [Google AI Studio](https://aistudio.google.com).  
> Lấy Qdrant URL + API key tại [Qdrant Cloud](https://cloud.qdrant.io).

---

## 3. Chạy tests

Không cần API key (test schema, rule engine, coverage scoring, routing — thuần Python):

```bash
pytest tests/ -v
```

---

## 4. Ingest testcase cũ (Excel) vào Qdrant

Đặt file Excel vào `data/`, sau đó chạy script ingest:

```bash
# VF34
python scripts/run_ingestion.py data/VF34_update.xlsx config/column_mapping.yaml

# Minio
python scripts/run_ingestion.py data/Minio.xlsx config/minio_column_mapping.yaml
```

Script tự tạo collection (nếu chưa có), embed từng row bằng Gemini, upsert vào Qdrant (idempotent — chạy lại không tạo trùng).

**Dùng file Excel khác:** copy một trong hai file `.yaml` trên, sửa giá trị bên phải mỗi dòng trong `columns:` cho khớp tên cột thật, rồi truyền `--mapping path/to/your_mapping.yaml` vào lệnh.

---

## 5. Chạy server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- Server: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- `--reload` tự restart khi sửa code (chỉ dùng khi dev)

---

## 6. Gọi API

### Kiểm tra health

```bash
curl http://localhost:8000/health
# {"status":"ok","qdrant":true}
```

### Sinh test case → JSON

```bash
curl -X POST http://localhost:8000/testcases/generate \
  -H "Content-Type: application/json" \
  -d '{"requirement_text": "mô tả requirement ở đây"}'
```

Response:
```json
{
  "testcases": [
    {
      "scenario_text": "...",
      "testcase": { "testcase_id": "TC-...", "title": "...", "steps": [...], ... },
      "coverage": { "final_score": 47.5, "classification": "New", ... }
    }
  ],
  "total_count": 5
}
```

### Sinh test case → Download Excel

```bash
curl -X POST http://localhost:8000/testcases/generate/export \
  -H "Content-Type: application/json" \
  -d '{"requirement_text": "mô tả requirement ở đây"}' \
  --output outputs/result.xlsx
```

File Excel cũng tự động lưu vào `outputs/testcases_YYYYMMDD_HHMMSS.xlsx` phía server.

### Windows (Command Prompt)

```cmd
curl -X POST http://localhost:8000/testcases/generate/export ^
  -H "Content-Type: application/json" ^
  -d "{\"requirement_text\": \"your requirement here\"}" ^
  --output outputs/result.xlsx
```

---

## 7. Thêm domain mới cho Rule Engine

1. Copy `app/rule_engine/domains/_template.py` sang file mới, ví dụ `infotainment.py`
2. Implement `generate_skeleton()` theo domain
3. `registry.py` tự động quét và đăng ký — không cần sửa thêm gì

---

## Cột Excel output

| Cột | Mô tả |
|---|---|
| TC ID | ID duy nhất của test case |
| Title | Tiêu đề test case |
| Domain | Functional domain (Climate Control, Body Control, ...) |
| Generation Path | `reuse` / `merge` / `rule_only` |
| Coverage Score | 0–100 |
| Classification | `High Match` / `Partial Match` / `New` |
| Best Match TC | TC cũ gần nhất (nếu có) |
| Scenario | Scenario input được decompose từ requirement |
| Preconditions | Điều kiện tiên quyết |
| Step No. / Action / Expected Result | Các bước test |
| Final Expected Result | Kết quả mong đợi tổng thể |

## B2B Multimodal Memory

Hệ thống bộ nhớ đa phương thức cho quy trình bán hàng B2B kéo dài và đa kênh (chat, email, meeting/call, file, ảnh). Kiến trúc gồm 4 tầng: ingestion → processing → storage → retrieval, triển khai bằng FastAPI, Qdrant (Vector DB), MinIO (Object Storage), và tích hợp Elasticsearch (keyword) + RAG (LLM) tùy chọn.

## Kiến trúc mức cao
- Ingestion: nhận dữ liệu từ text, file (pdf/docx/txt), email, chat, audio, image.
- Processing: chuẩn hóa, chunking, embedding; OCR (image) bằng Tesseract; STT audio (stub, có thể thay bằng Whisper).
- Storage: Qdrant (vector), MinIO (object gốc), Elasticsearch (BM25 từ khóa) + payload metadata.
- Retrieval: hybrid search (vector + keyword + rescoring) và tổng hợp câu trả lời kiểu RAG (OpenAI tùy chọn) có trích nguồn.

## Công nghệ sử dụng
- **Ngôn ngữ & Runtime**: Python 3.11+, Uvicorn (ASGI server)
- **Web Framework**: FastAPI
- **Vector Database**: Qdrant
- **Object Storage**: MinIO (S3 compatible)
- **Keyword Search**: Elasticsearch (BM25)
- **Embeddings**: Sentence-Transformers
- **OCR**: Tesseract OCR (cài native) + Pillow + pytesseract
- **Document parsing**: pypdf, python-docx
- **Audio STT**: stub (có thể thay bằng Whisper/faster-whisper)
- **RAG/LLM**: OpenAI (qua `OPENAI_API_KEY`)
- **Orchestration**: Docker Compose (Qdrant, MinIO, Elasticsearch)

## Cài đặt nhanh (Windows)
1) Tạo `.env` (nếu bạn chưa có):
```powershell
cd C:\Users\ASUS\Desktop\b2b-multimodal-memory
notepad .env
```
Ví dụ nội dung tối thiểu:
```env
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=mm_memory
VECTOR_DIM=384
EMBEDDING_PROVIDER=random

MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=mm-raw
MINIO_SECURE=false

ES_URL=http://localhost:9200
ES_INDEX=mm_memory

API_PORT=8080
```

2) Khởi động hạ tầng (Qdrant, MinIO, Elasticsearch):
```powershell
docker compose up -d
```

3) Cài dependencies (khuyến nghị venv):
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

4) Chạy API:
```powershell
uvicorn src.api.main:app --reload --port 8080
```
Mở: http://localhost:8080/docs

## Cấu trúc thư mục
```
multimodal-b2b-memory/
├── .env(.example)
├── docker-compose.yml
├── requirements.txt
├── README.md
├── data/
├── notebooks/
└── src/
    ├── api/
    │   ├── main.py
    │   ├── schemas.py
    │   └── routers/
    │       ├── ingest_routes.py
    │       └── search_routes.py
    ├── core/
    │   ├── config.py            # .env loader: Qdrant/MinIO/ES/OpenAI/Tesseract
    │   ├── models.py            # Embedding provider (random | sentence-transformers)
    │   └── storage.py           # Qdrant/MinIO + Elasticsearch connector
    ├── ingestion/
    │   ├── email_ingestor.py    # placeholder connect Gmail/Graph
    │   ├── chat_ingestor.py     # placeholder connect Slack/Teams/Zalo
    │   └── file_uploader.py
    ├── processing/
    │   ├── pipeline.py          # orchestrate ingest → chunk → embed → upsert → ES index
    │   ├── text_processor.py    # clean + chunk
    │   ├── document_processor.py# pdf/docx extract
    │   ├── audio_processor.py   # STT stub (có thể thay Whisper)
    │   └── image_processor.py   # OCR Tesseract
    └── retrieval/
        ├── search.py            # vector(Qdrant)+keyword(ES)+rescoring
        ├── text_rank.py         # simple rescoring
        └── generator.py         # RAG (OpenAI), fallback nếu không có API key
```

## Biến môi trường chính (.env)
- QDRANT_URL, QDRANT_COLLECTION, VECTOR_DIM (mặc định 384)
- EMBEDDING_PROVIDER: `random` | `sentence` (cần cài sentence-transformers nếu dùng)
- MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET, MINIO_SECURE
- ES_URL, ES_INDEX, (ES_USERNAME/ES_PASSWORD nếu bật security)
- OPENAI_API_KEY, OPENAI_MODEL (mặc định `gpt-4o-mini`)
- TESSERACT_CMD: đường dẫn `tesseract.exe` trên Windows, ví dụ:
  - `TESSERACT_CMD="C:\\Program Files\\Tesseract-OCR\\tesseract.exe"`

## Endpoints chính
- POST `/ingest/text`
  - body (JSON):
    ```json
    {
      "title": "Demo",
      "text": "Nội dung cuộc họp...",
      "customer_id": "CUS-001",
      "channel": "text",
      "thread_id": "TH-1",
      "interaction_id": "INT-1",
      "timestamp": "2024-10-01T10:00:00Z",
      "participants": ["sales@company.com", "client@x.com"]
    }
    ```
  - Kết quả: `{ "ids": ["<uuid>", ...] }`

- POST `/ingest/file` (multipart form)
  - form-data: `file: <pdf|docx|txt>`
  - Lưu file vào MinIO, trích văn bản, chunk → embed → upsert Qdrant, index ES

- POST `/ingest/email`
  - body (JSON): giống text nhưng có thêm `subject`, `message_id`, `in_reply_to`, `channel: "email"`

- POST `/ingest/chat`
  - body (JSON): `platform`, `text`, `customer_id`..., `channel: "chat"`

- POST `/ingest/audio` (multipart form)
  - form-data: `file: <wav|mp3>`
  - STT stub (trả rỗng nếu chưa tích hợp Whisper), chunk → embed → upsert Qdrant, index ES

- POST `/ingest/image` (multipart form)
  - form-data: `file: <png|jpg>`
  - OCR bằng Tesseract, chunk → embed → upsert Qdrant, index ES

- POST `/search`
  - body (JSON):
    ```json
    {
      "query": "Giá sản phẩm A bàn lúc nào?",
      "top_k": 5,
      "customer_id": "CUS-001",
      "channel": "email",
      "date_from": "2024-01-01",
      "date_to": "2024-12-31"
    }
    ```
  - Trả về: danh sách chunks (có metadata nguồn) + câu trả lời tổng hợp (RAG nếu có OpenAI API key, fallback nếu không).

## Ghi chú triển khai
- Embedding mặc định là `random` (demo). Để dùng thật:
  - Mở comment `sentence-transformers` trong `requirements.txt` và đặt `EMBEDDING_PROVIDER=sentence`.
- OCR yêu cầu cài Tesseract (Windows):
  - `winget install -e --id UB-Mannheim.TesseractOCR`
  - Set `.env` `TESSERACT_CMD` đúng đường dẫn `tesseract.exe`.
- RAG thật:
  - Đặt `OPENAI_API_KEY` trong `.env`. Nếu không có, hệ thống dùng fallback (trả về top match trích nguồn).
- Hybrid search:
  - Khi có `ES_URL`, hệ thống tự tạo index và index dữ liệu vào Elasticsearch (BM25) song song Qdrant.

## Khắc phục sự cố nhanh
- `docker: not recognized` → Cài Docker Desktop, mở app cho chạy, mở PowerShell mới, kiểm tra `docker --version`.
- `tesseract not found` → Cài Tesseract và đặt `TESSERACT_CMD` đúng, khởi động lại API.
- Lỗi kết nối Qdrant/ES/MinIO → kiểm tra `docker compose ps`, các cổng `6333/9000/9200` đang lắng nghe.

## Lộ trình nâng cấp (gợi ý)
- Tích hợp Whisper cho STT (diarization), CLIP/BLIP cho image embeddings.
- Chuẩn hoá schema session/interaction để hỗ trợ multi-turn mạnh hơn (timeline, participants, role diarization).
- Re-ranking nâng cao (Cross-Encoder), caching và ACL/tenancy.


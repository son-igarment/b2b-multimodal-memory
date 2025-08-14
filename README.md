# b2b-multimodal-memory

Multimodal Memory cho bài toán B2B (ingestion → processing → storage → retrieval) với FastAPI, Qdrant (Vector DB) và MinIO (Object Storage).

## Kiến trúc mức cao
- Ingestion: nhận dữ liệu từ email/chat/upload file (MVP: upload text/pdf/docx)
- Processing: chuẩn hóa, chunking, embedding, tóm tắt (stub)
- Storage: Qdrant (vector), MinIO (object), metadata (inline)
- Retrieval: semantic search + tổng hợp trả lời (stub RAG)

## Chạy nhanh
1) Tạo file `.env` từ mẫu:
```bash
copy .env.example .env
```

2) Khởi động hạ tầng:
```bash
docker compose up -d
```

3) Cài dependencies (khuyến nghị venv):
```bash
pip install -r requirements.txt
```

4) Chạy API:
```bash
uvicorn src.api.main:app --reload --port 8080
```

Open: http://localhost:8080/docs

## Cấu trúc thư mục
```
multimodal-b2b-memory/
├── .env.example
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
    │   ├── config.py
    │   ├── models.py
    │   └── storage.py
    ├── ingestion/
    │   ├── email_ingestor.py
    │   ├── chat_ingestor.py
    │   └── file_uploader.py
    ├── processing/
    │   ├── pipeline.py
    │   ├── text_processor.py
    │   └── document_processor.py
    └── retrieval/
        ├── search.py
        └── generator.py
```

## MVP API
- POST `/ingest/text` — nạp text (title, text, customer_id)
- POST `/ingest/file` — nạp file pdf/docx/txt
- POST `/search` — semantic search + tổng hợp câu trả lời (stub)

## Ghi chú
- Embedding mặc định dùng provider `random` (nhẹ, chỉ demo). Đổi sang Sentence-Transformers bằng cách đặt `EMBEDDING_PROVIDER=sentence`.
- Xem `src/core/models.py` và `src/core/storage.py` để cấu hình Qdrant/MinIO.

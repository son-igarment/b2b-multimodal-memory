from __future__ import annotations

from typing import List, Optional
from ..core.config import settings
from ..api.schemas import ChunkResult


def _format_context(chunks: List[ChunkResult], max_chars: int = 2000) -> str:
    parts: List[str] = []
    remaining: int = max_chars
    for c in chunks:
        src = c.metadata.get("raw_content_path") or c.metadata.get("title") or ""
        piece = f"[source:{src}] {c.text}\n"
        if len(piece) <= remaining:
            parts.append(piece)
            remaining -= len(piece)
        else:
            parts.append(piece[:remaining])
            break
    return "".join(parts)


def _call_openai(prompt: str) -> Optional[str]:
    api_key = settings.openai_api_key
    if not api_key:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers using Vietnamese. Cite sources when possible."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        return resp.choices[0].message.content
    except Exception:
        return None


def generate_answer(query: str, chunks: List[ChunkResult]) -> Optional[str]:
    if not chunks:
        return None
    context = _format_context(chunks)
    prompt = (
        "Dựa trên các trích đoạn sau, hãy trả lời ngắn gọn câu hỏi. "
        "Trích dẫn nguồn ở cuối câu bằng [source:...] nếu có.\n\n"
        f"Câu hỏi: {query}\n\n"
        f"Ngữ cảnh:\n{context}"
    )
    answer = _call_openai(prompt)
    if answer:
        return answer
    # Fallback rất đơn giản nếu không có OpenAI API key
    top = chunks[0]
    src = top.metadata.get("raw_content_path") or top.metadata.get("title") or ""
    return f"(Fallback) Tham khảo: [source:{src}] {top.text[:400]}..."



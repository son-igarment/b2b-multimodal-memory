from __future__ import annotations

from typing import List, Tuple


def transcribe_audio(audio_bytes: bytes, language: str = "vi") -> Tuple[str, List[Tuple[float, float, str]]]:
    """Cố gắng dùng faster-whisper nếu đã cài, nếu không fallback stub.
    Trả về: (toàn bộ transcript, list các đoạn (start, end, text)).
    """
    try:
        from faster_whisper import WhisperModel  # type: ignore
        # Tự chọn size nhỏ để chạy CPU, hoặc đọc từ env nếu cần
        model = WhisperModel("small", device="cpu", compute_type="int8")
        import io
        audio_io = io.BytesIO(audio_bytes)
        segments, _info = model.transcribe(audio_io, language=language)
        full_text: str = ""
        diar: List[Tuple[float, float, str]] = []
        for seg in segments:
            full_text += seg.text.strip() + "\n"
            diar.append((float(seg.start or 0.0), float(seg.end or 0.0), seg.text.strip()))
        return full_text.strip(), diar
    except Exception:
        # Stub fallback nếu chưa cài hoặc lỗi runtime
        return "", []



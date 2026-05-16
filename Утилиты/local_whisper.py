"""
Локальная транскрибация аудио через distil-whisper на RTX 5070.

Модель: distil-whisper/small (49M параметров, в 6× быстрее оригинала)
Вывод: VTT-файл с таймкодами
"""

import os
import re
import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline


# Глобальные переменные для кэширования модели
_model = None
_processor = None
_pipe = None


def _load_model():
    """Загружает distil-whisper один раз и кэширует в памяти."""
    global _model, _processor, _pipe
    if _pipe is not None:
        return _pipe

    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    # Для русского языка используем whisper-small (многоязычный, ~900MB)
    # Альтернативы: "openai/whisper-base" (~300MB, быстрее, но менее точный)
    # "distil-whisper/distil-large-v3" (~1.5GB, быстрый distil-вариант)
    model_id = "openai/whisper-small"

    print(f"🤖 Загрузка {model_id} на {device}...")

    _model = AutoModelForSpeechSeq2Seq.from_pretrained(
        model_id,
        torch_dtype=torch_dtype,
        low_cpu_mem_usage=True,
        use_safetensors=True,
    )
    _model.to(device)

    _processor = AutoProcessor.from_pretrained(model_id)

    _pipe = pipeline(
        "automatic-speech-recognition",
        model=_model,
        tokenizer=_processor.tokenizer,
        feature_extractor=_processor.feature_extractor,
        chunk_length_s=30,
        batch_size=16,
        dtype=torch_dtype,
        device=device,
        ignore_warning=True,
    )

    print(f"✅ Модель загружена. GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")
    return _pipe


def transcribe_to_text(audio_path: str, pipe=None) -> str:
    """
    Транскрибирует аудио в текст.
    Возвращает строку с распознанным текстом.
    """
    pipe = pipe or _load_model()
    result = pipe(audio_path, return_timestamps=False, generate_kwargs={"language": "russian"})
    return result.get("text", "").strip()


def transcribe_to_vtt(audio_path: str, pipe=None) -> str:
    """
    Транскрибирует аудио и возвращает VTT-формат с таймкодами.
    """
    pipe = pipe or _load_model()
    result = pipe(audio_path, return_timestamps=True, generate_kwargs={"language": "russian"})

    chunks = result.get("chunks", [])
    if not chunks:
        return transcribe_to_text(audio_path)

    lines = ["WEBVTT", ""]
    for chunk in chunks:
        start = chunk.get("timestamp", [0, 0])[0]
        end = chunk.get("timestamp", [0, 0])[1]
        text = chunk.get("text", "").strip()

        if start is None or end is None:
            continue

        # Формат таймкодов: HH:MM:SS.mmm
        def fmt(t):
            if t is None:
                return "00:00:00.000"
            h = int(t // 3600)
            m = int((t % 3600) // 60)
            s = t % 60
            return f"{h:02d}:{m:02d}:{s:06.3f}"

        lines.append(f"{fmt(start)} --> {fmt(end)}")
        lines.append(text)
        lines.append("")

    return "\n".join(lines)


def save_vtt(vtt_text: str, output_path: str):
    """Сохраняет VTT-текст в файл."""
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(vtt_text)


def parse_vtt_to_text(vtt_text: str) -> str:
    """Преобразует VTT обратно в plain text (убирает таймкоды)."""
    lines = []
    for line in vtt_text.splitlines():
        line = line.strip()
        if not line or line.upper() == "WEBVTT":
            continue
        if re.match(r'^\d{2}:\d{2}:\d{2}\.\d{3}\s*-->', line):
            continue
        if re.match(r'^\d+$', line):
            continue
        lines.append(line)
    return " ".join(lines)

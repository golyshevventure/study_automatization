"""
Извлечение аудио из Kinescope-видео.

Шаги:
1. Перехватить mp4-ссылку через Playwright (как с VTT)
2. Скачать mp4 через requests
3. Конвертировать mp4 → wav (mono, 16kHz) через ffmpeg
"""

import os
import re
import subprocess
import requests


def extract_audio_from_mp4(video_url: str, output_dir: str = "data/audio") -> str:
    """
    Извлекает аудио из видео (MP4 или M3U8/HLS) в wav (mono, 16kHz) для Whisper.
    FFmpeg сам скачивает поток — поддерживает и прямые MP4, и HLS (m3u8).
    Возвращает путь к wav-файлу.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Имя файла из URL
    base_name = re.sub(r"[^\w]", "_", video_url.split("/")[-1].split("?")[0])[:40]
    if base_name.endswith("_m3u8") or base_name.endswith("_master"):
        base_name = base_name[:35]
    wav_path = os.path.join(output_dir, f"{base_name}.wav")

    if os.path.exists(wav_path):
        return wav_path

    # FFmpeg сам скачивает и MP4, и M3U8 (HLS)
    cmd = [
        "ffmpeg",
        "-y",
        "-fflags",
        "+discardcorrupt",
        "-i",
        video_url,
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-t",
        "7200",  # ограничение 2 часа на всякий случай
        wav_path,
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    return wav_path


def cleanup_audio_files(output_dir: str = "data/audio"):
    """Удаляет все wav/mp4 файлы из папки аудио."""
    if not os.path.isdir(output_dir):
        return
    for f in os.listdir(output_dir):
        if f.endswith(".wav") or f.endswith(".mp4") or f.endswith(".tmp.mp4"):
            os.remove(os.path.join(output_dir, f))

"""
Извлечение аудио из Kinescope-видео.

Шаги:
1. Разрешить short URL Kinescope → master.m3u8 (через HTML парсинг)
2. FFmpeg скачивает поток (MP4/M3U8) → wav
"""

import os
import re
import subprocess
import requests


def resolve_kinescope_video_url(video_url: str) -> str:
    """
    Преобразует short URL Kinescope (https://kinescope.io/XXXX)
    в прямую ссылку на master.m3u8.
    Если URL уже содержит .m3u8 или .mp4 — возвращает как есть.
    """
    if ".m3u8" in video_url or ".mp4" in video_url:
        return video_url

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    r = requests.get(video_url, headers=headers, timeout=15)
    r.raise_for_status()
    html = r.text

    # Паттерн 1: playerOptions.playlist[...].sources.hls.src
    m = re.search(r'"src"\s*:\s*"(https://kinescope\.io/[^"]+master\.m3u8)"', html)
    if m:
        return m.group(1)

    # Паттерн 2: playerOptions с UUID
    m = re.search(r'"id"\s*:\s*"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"', html)
    if m:
        uuid = m.group(1)
        return f"https://kinescope.io/{uuid}/master.m3u8"

    # Fallback: ищем любой master.m3u8
    m = re.search(r'(https://kinescope\.io/[^"\s]+master\.m3u8)', html)
    if m:
        return m.group(1)

    raise ValueError(f"Не удалось извлечь master.m3u8 из {video_url}")


def extract_audio_from_mp4(video_url: str, output_dir: str = "data/audio") -> str:
    """
    Извлекает аудио из видео (MP4 или M3U8/HLS) в wav (mono, 16kHz) для Whisper.
    Автоматически разрешает short URL Kinescope → master.m3u8.
    FFmpeg сам скачивает поток.
    Возвращает путь к wav-файлу.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Разрешаем Kinescope short URL → master.m3u8
    resolved_url = resolve_kinescope_video_url(video_url)

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
        resolved_url,
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

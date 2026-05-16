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


def extract_audio_from_mp4(mp4_url: str, output_dir: str = "data/audio") -> str:
    """
    Скачивает mp4 и конвертирует в wav (mono, 16kHz) для Whisper.
    Возвращает путь к wav-файлу.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Имя файла из URL
    base_name = re.sub(r'[^\w]', '_', mp4_url.split('/')[-1].split('?')[0])[:40]
    wav_path = os.path.join(output_dir, f"{base_name}.wav")

    if os.path.exists(wav_path):
        return wav_path

    # Скачиваем mp4 во временный файл
    tmp_mp4 = os.path.join(output_dir, f"{base_name}.tmp.mp4")
    r = requests.get(mp4_url, timeout=120, stream=True)
    r.raise_for_status()
    with open(tmp_mp4, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)

    # Конвертируем в wav: mono, 16kHz (оптимально для Whisper)
    cmd = [
        "ffmpeg", "-y", "-i", tmp_mp4,
        "-vn", "-acodec", "pcm_s16le",
        "-ac", "1", "-ar", "16000",
        wav_path
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Удаляем временный mp4
    os.remove(tmp_mp4)

    return wav_path


def cleanup_audio_files(output_dir: str = "data/audio"):
    """Удаляет все wav/mp4 файлы из папки аудио."""
    if not os.path.isdir(output_dir):
        return
    for f in os.listdir(output_dir):
        if f.endswith(".wav") or f.endswith(".mp4") or f.endswith(".tmp.mp4"):
            os.remove(os.path.join(output_dir, f))

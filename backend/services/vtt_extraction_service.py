"""Сервис извлечения VTT-субтитров из Kinescope-видео."""

import re

import requests


class VTTExtractionService:
    """Извлекает VTT из Kinescope HTML и парсит в plain text."""

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://netology.ru",
    }

    @staticmethod
    def extract_vtt(video_url: str) -> str:
        """
        Извлекает VTT-субтитры из Kinescope-видео.
        Парсит HTML embed-страницу, ищет .vtt URL, скачивает и конвертирует в текст.
        Возвращает пустую строку, если субтитров нет.
        """
        try:
            resp = requests.get(video_url, headers=VTTExtractionService.HEADERS, timeout=15)
            if resp.status_code != 200:
                return ""

            vtt_urls = re.findall(r'https?://[^"\'\s]+\.vtt[^"\'\s]*', resp.text)
            if not vtt_urls:
                return ""

            vtt_url = vtt_urls[0]
            vtt_resp = requests.get(vtt_url, timeout=15)
            if vtt_resp.status_code != 200:
                return ""

            return VTTExtractionService._parse_vtt(vtt_resp.text)
        except Exception:
            return ""

    @staticmethod
    def _parse_vtt(vtt_text: str) -> str:
        """Парсит WebVTT в plain text."""
        lines = vtt_text.splitlines()
        result = []
        for line in lines:
            line = line.strip()
            if not line or line.upper() == "WEBVTT":
                continue
            if re.match(r"^\d{2}:\d{2}:\d{2}\.\d{3}\s*-->", line):
                continue
            if re.match(r"^\d+$", line):
                continue
            if line.upper().startswith(("NOTE", "REGION", "STYLE")):
                continue
            result.append(line)
        return " ".join(result)

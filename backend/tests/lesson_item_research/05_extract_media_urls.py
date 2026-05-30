"""
Извлечение прямых URL медиа из lesson_items.

Для каждого типа:
  - video/webinar: HLS master.m3u8 через Kinescope embed
  - attachment: прямые ссылки из files[]
  - text/longread/task: content (markdown/html)
  - test/poll/quiz: пока без прямого контента

Результаты: backend/api_tests_etc/lesson_items/extracted_media_urls.json
"""

import json
import os
import re
import sys
from pathlib import Path

import httpx

PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_DIR = PROJECT_ROOT / "backend" / "api_tests_etc" / "lesson_items"


def extract_kinescope_hls(video_url: str) -> dict | None:
    """Парсит embed-страницу Kinescope и извлекает HLS src."""
    video_id = video_url.rstrip("/").split("/")[-1]
    try:
        resp = httpx.get(
            f"https://kinescope.io/embed/{video_id}",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://netology.ru/",
            },
            timeout=15.0,
            follow_redirects=True,
        )
        if resp.status_code != 200:
            return None
        text = resp.text
        match = re.search(r'var playerOptions = ({.*?});', text, re.DOTALL)
        if not match:
            return None
        data = json.loads(match.group(1))
        playlist = data.get("playlist", [])
        if not playlist:
            return None
        sources = playlist[0].get("sources", {})
        hls = sources.get("hls", {})
        return {
            "hls_src": hls.get("src"),
            "poster": playlist[0].get("posterInPreview"),
            "title": playlist[0].get("title"),
            "duration": playlist[0].get("meta", {}).get("duration"),
            "video_id": playlist[0].get("id"),
            "qualities": list(playlist[0].get("qualityLabels", {}).keys()),
        }
    except Exception as exc:
        return {"error": str(exc)}


def extract_vtt_urls(video_url: str) -> list:
    """Пытается найти VTT субтитры для Kinescope видео."""
    video_id = video_url.rstrip("/").split("/")[-1]
    results = []
    client = httpx.Client(timeout=10.0, follow_redirects=True)

    # Варианты URL для субтитров
    urls_to_try = [
        f"https://kinescope.io/api/v1/videos/{video_id}/subtitles",
        f"https://kinescope.io/api/videos/{video_id}/subtitles",
        f"https://kinescope.io/{video_id}/subtitles.vtt",
        f"https://kinescope.io/{video_id}/subtitles",
    ]
    for url in urls_to_try:
        try:
            resp = client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200:
                results.append({"url": url, "status": 200, "content_type": resp.headers.get("content-type")})
        except Exception:
            pass
    client.close()
    return results


def main():
    # Загружаем детальные lesson_items
    with open(OUTPUT_DIR / "05_all_detailed.json", encoding="utf-8") as f:
        detailed = json.load(f)

    results = []
    for item in detailed:
        if item["status_code"] != 200 or not item["data"]:
            continue

        data = item["data"]
        li_id = data.get("id")
        li_type = data.get("type")
        record = {
            "id": li_id,
            "type": li_type,
            "title": data.get("title"),
        }

        if li_type in ("video", "webinar"):
            video_url = data.get("video_url")
            record["video_url"] = video_url
            if video_url:
                print(f"🎬 {li_id} [{li_type}] → Kinescope: {video_url}")
                kine = extract_kinescope_hls(video_url)
                record["kinescope"] = kine
                if kine and kine.get("hls_src"):
                    print(f"    HLS: {kine['hls_src']}")
                # VTT
                vtt = extract_vtt_urls(video_url)
                record["vtt_attempts"] = vtt
                if vtt:
                    print(f"    VTT found: {vtt}")

        elif li_type == "attachment":
            files = data.get("files", [])
            record["files"] = [
                {"name": f.get("name"), "extension": f.get("extension"), "link": f.get("link"), "size": f.get("size")}
                for f in files
            ]
            print(f"📎 {li_id} [{li_type}] → {len(files)} файл(ов)")

        elif li_type in ("text", "longread", "task"):
            content = data.get("content")
            record["content_type"] = data.get("content_type")
            if isinstance(content, str):
                record["content_length"] = len(content)
                record["content_preview"] = content[:200]
            elif isinstance(content, dict):
                record["content_length"] = len(json.dumps(content))
                record["content_preview"] = json.dumps(content, ensure_ascii=False)[:200]
                record["content_is_structured"] = True
            else:
                record["content_length"] = 0
                record["content_preview"] = str(content)[:200]
            print(f"📝 {li_id} [{li_type}] → {record['content_length']} символов")

        else:
            print(f"❓ {li_id} [{li_type}] → пока не обрабатываем")

        results.append(record)

    output_path = OUTPUT_DIR / "06_extracted_media_urls.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Сохранено: {output_path}")

    # Сводка
    print("\n📊 Сводка:")
    hls_ok = sum(1 for r in results if r.get("kinescope", {}).get("hls_src"))
    files_ok = sum(1 for r in results if r.get("files"))
    content_ok = sum(1 for r in results if r.get("content_length", 0) > 0)
    print(f"   HLS извлечено: {hls_ok}")
    print(f"   Файловые ссылки: {files_ok}")
    print(f"   Текстовый контент: {content_ok}")


if __name__ == "__main__":
    main()

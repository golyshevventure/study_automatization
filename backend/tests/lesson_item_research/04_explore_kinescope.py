"""
Исследование извлечения прямых URL видео из Kinescope.

Подходы:
1. oEmbed API
2. Embed-страница (парсинг JSON/initial state)
3. GraphQL API
4. Проверка доступности VTT (субтитров)

Результаты: backend/api_tests_etc/lesson_items/kinescope_*.json
"""

import json
import os
import sys
from pathlib import Path

import httpx

PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_DIR = PROJECT_ROOT / "backend" / "api_tests_etc" / "lesson_items"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def save_json(name: str, data):
    path = OUTPUT_DIR / f"{name}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  💾 {path.name}")


def explore_video(video_url: str, label: str):
    print(f"\n🎬 {label}: {video_url}")
    results = {"video_url": video_url, "label": label}

    video_id = video_url.rstrip("/").split("/")[-1]
    print(f"   Video ID: {video_id}")

    client = httpx.Client(timeout=15.0, follow_redirects=True, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Referer": "https://netology.ru/",
    })

    # ── 1. oEmbed ────────────────────────────────────────────────────────────
    print("   1. oEmbed...", end=" ")
    try:
        resp = client.get(f"https://kinescope.io/oembed", params={
            "url": video_url,
            "format": "json",
        })
        print(resp.status_code)
        results["oembed"] = {
            "status_code": resp.status_code,
            "data": resp.json() if resp.status_code == 200 else resp.text[:300],
        }
    except Exception as exc:
        print(f"ERROR: {exc}")
        results["oembed"] = {"error": str(exc)}

    # ── 2. Embed страница ────────────────────────────────────────────────────
    print("   2. Embed page...", end=" ")
    try:
        resp = client.get(f"https://kinescope.io/embed/{video_id}")
        print(resp.status_code)
        text = resp.text
        results["embed_page"] = {
            "status_code": resp.status_code,
            "content_length": len(text),
        }
        # Ищем window.__INITIAL_STATE__ или аналогичные JSON-данные
        for marker in ["window.__INITIAL_STATE__", "window.__DATA__", "videoData", "data-video"]:
            if marker in text:
                print(f"      ✅ Found marker: {marker}")
                results["embed_page"]["marker_found"] = marker
                # Извлекаем JSON рядом с маркером
                idx = text.find(marker)
                snippet = text[idx:idx+500]
                results["embed_page"]["snippet"] = snippet
                break
        else:
            print("      ❌ No markers found")
            results["embed_page"]["marker_found"] = None

        # Ищем m3u8 или mp4 напрямую в HTML
        if ".m3u8" in text:
            print("      ✅ Found .m3u8 in HTML")
            results["embed_page"]["has_m3u8"] = True
            # Извлекаем URL
            idx = text.find(".m3u8")
            start = text.rfind('"', 0, idx) + 1
            end = text.find('"', idx)
            m3u8_url = text[start:end]
            results["embed_page"]["m3u8_url"] = m3u8_url
        if ".mp4" in text:
            print("      ✅ Found .mp4 in HTML")
            results["embed_page"]["has_mp4"] = True
    except Exception as exc:
        print(f"ERROR: {exc}")
        results["embed_page"] = {"error": str(exc)}

    # ── 3. GraphQL API ───────────────────────────────────────────────────────
    print("   3. GraphQL...", end=" ")
    try:
        resp = client.post(
            "https://kinescope.io/graphql",
            json={
                "query": """
                    query GetVideo($id: ID!) {
                        video(id: $id) {
                            id
                            title
                            description
                            duration
                            files { url quality }
                            assets { url kind }
                        }
                    }
                """,
                "variables": {"id": video_id},
            },
            headers={"Content-Type": "application/json"},
        )
        print(resp.status_code)
        results["graphql"] = {
            "status_code": resp.status_code,
            "data": resp.json() if resp.status_code == 200 else resp.text[:300],
        }
    except Exception as exc:
        print(f"ERROR: {exc}")
        results["graphql"] = {"error": str(exc)}

    # ── 4. Прямой API v1 (если есть) ─────────────────────────────────────────
    print("   4. API v1...", end=" ")
    try:
        resp = client.get(f"https://kinescope.io/api/v1/videos/{video_id}")
        print(resp.status_code)
        results["api_v1"] = {
            "status_code": resp.status_code,
            "data": resp.json() if resp.status_code == 200 else resp.text[:300],
        }
    except Exception as exc:
        print(f"ERROR: {exc}")
        results["api_v1"] = {"error": str(exc)}

    # ── 5. VTT субтитры ──────────────────────────────────────────────────────
    print("   5. VTT check...", end=" ")
    try:
        # Пробуем стандартный путь для субтитров Kinescope
        vtt_url = f"https://kinescope.io/{video_id}/subtitles"
        resp = client.get(vtt_url)
        print(f"{resp.status_code} ({vtt_url})")
        results["vtt"] = {
            "url": vtt_url,
            "status_code": resp.status_code,
            "content_type": resp.headers.get("content-type"),
        }
    except Exception as exc:
        print(f"ERROR: {exc}")
        results["vtt"] = {"error": str(exc)}

    client.close()
    return results


def main():
    # Берём несколько video_url из собранных lesson_items
    video_urls = [
        ("video_1", "https://kinescope.io/tQh7UAcuDDQAboyHfQwC5c"),
        ("video_2", "https://kinescope.io/dbSLrR1LWpNtrnwK2aXCGw"),
        ("webinar_1", "https://kinescope.io/tMovmrw31bN9CrcsEcsyuf"),
    ]

    all_results = []
    for label, url in video_urls:
        res = explore_video(url, label)
        all_results.append(res)
        save_json(f"kinescope_{label}", res)

    save_json("kinescope_all_results", all_results)
    print(f"\n✅ Kinescope исследование завершено. Результаты: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()

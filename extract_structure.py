import sys
from bs4 import BeautifulSoup
import json

def extract_structure(html_path, output_path):
    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
    
    for tag in soup(["script", "style", "svg", "noscript", "iframe"]):
        tag.decompose()
    
    data = {
        "title": soup.title.get_text(strip=True) if soup.title else "",
        "text_blocks": [],
        "links": [],
        "data_attributes": []
    }
    
    for el in soup.find_all(attrs={"data-testid": True}):
        text = el.get_text(strip=True)
        if text and len(text) > 2:
            data["text_blocks"].append({
                "tag": el.name,
                "data-testid": el.get("data-testid"),
                "text": text[:200],
                "class": el.get("class", [])[:3]
            })
    
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "lesson" in href or "item" in href or "program" in href:
            data["links"].append({
                "href": href,
                "text": a.get_text(strip=True)[:100]
            })
    
    for el in soup.find_all(attrs={"data-lesson-id": True}):
        data["data_attributes"].append({
            "data-lesson-id": el.get("data-lesson-id"),
            "text_preview": el.get_text(strip=True)[:150]
        })
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Структура сохранена: {output_path}")
    print(f"   Блоков: {len(data['text_blocks'])}, Ссылок: {len(data['links'])}, data-lesson-id: {len(data['data_attributes'])}")

if __name__ == "__main__":
    extract_structure(sys.argv[1], sys.argv[2])

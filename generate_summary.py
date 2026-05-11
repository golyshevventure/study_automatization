import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1"

def load_prompt(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def generate_summary(lecture_text: str, subject: str) -> str:
    system_prompt = load_prompt("prompts/system.txt")
    
    response = requests.post(
        f"{BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://localhost",
            "X-Title": "Study Automation Agent"
        },
        json={
            "model": "poolside/laguna-m.1:free",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Предмет: {subject}\n\nТекст лекции:\n{lecture_text}"}
            ],
            "max_tokens": 2000,
            "temperature": 0.4
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        content = data["choices"][0]["message"].get("content")
        if content:
            return content
        else:
            return "⚠️ Модель вернула пустой ответ (перегружена)"
    else:
        return f"❌ Ошибка {response.status_code}: {response.text[:300]}"

if __name__ == "__main__":
    # Тестовый текст — замени на реальный текст лекции или субтитры
    test_lecture = """
    Введение в корпоративные финансы. Корпоративные финансы — это область финансов, которая занимается решениями о том, как компании привлекают капитал, инвестируют его и распределяют прибыль. Основная цель — максимизация стоимости фирмы для акционеров. Ключевые понятия: временная стоимость денег (time value of money), дисконтирование, NPV (чистая приведённая стоимость), IRR (внутренняя норма доходности). NPV рассчитывается как сумма дисконтированных денежных потоков минус первоначальные инвестиции. Формула: NPV = Σ(CF_t / (1+r)^t) - I_0. Если NPV > 0 — проект принимаем. IRR — это ставка дисконтирования, при которой NPV = 0. Пример: компания рассматривает покупку оборудования за 1 млн рублей. Ожидаемые денежные потоки: год 1 — 400 тыс, год 2 — 500 тыс, год 3 — 300 тыс. Ставка дисконтирования 10%. NPV = 400/1.1 + 500/1.1^2 + 300/1.1^3 - 1000 = ... 
    """
    
    print("=" * 60)
    print("Генерация конспекта...")
    print("=" * 60)
    
    result = generate_summary(test_lecture, "Корпоративные финансы")
    
    print("\nРЕЗУЛЬТАТ:\n")
    print(result)
    
    # Сохраняем в файл
    os.makedirs("output", exist_ok=True)
    with open("output/test_summary.md", "w", encoding="utf-8") as f:
        f.write(result)
    
    print(f"\n💾 Сохранено в output/test_summary.md")

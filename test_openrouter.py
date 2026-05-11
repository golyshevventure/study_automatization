import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1"

def test_model(model_name, model_label):
    print(f"\n{'=' * 50}")
    print(f"Тест: {model_label}")
    print(f"ID: {model_name}")
    print(f"{'=' * 50}")
    
    response = requests.post(
        f"{BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://localhost",
            "X-Title": "Study Automation Agent"
        },
        json={
            "model": model_name,
            "messages": [
                {
                    "role": "system",
                    "content": "Ты — ассистент студента 1 курса бакалавриата 'Финансы и анализ данных'. Делай краткие, ёмкие конспекты на русском языке."
                },
                {
                    "role": "user",
                    "content": "Сделай конспект из этого текста (макс 150 слов):\n\nВведение в статистику. Статистика — наука о сборе, анализе и интерпретации данных. Основные понятия: генеральная совокупность, выборка, вариация, представительность. Методы описательной статистики: среднее арифметическое, медиана, мода, стандартное отклонение, дисперсия. Графические методы: гистограмма, полигон, кумулята, диаграмма рассеяния. Нормальное распределение и его свойства: симметрия, колоколообразность, правило 3 сигм. Центральная предельная теорема: при n > 30 распределение выборочного среднего стремится к нормальному независимо от формы распределения генеральной совокупности."
                }
            ],
            "max_tokens": 500,
            "temperature": 0.3
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        content = data["choices"][0]["message"].get("content")
        
        if content:
            print(f"\n✅ Успех!\n")
            print(content[:600] + "..." if len(content) > 600 else content)
            return True
        else:
            print(f"\n⚠️ Ответ пустой (модель перегружена)")
            print(f"Структура: {data['choices'][0]['message']}")
            return False
    else:
        print(f"\n❌ Ошибка {response.status_code}: {response.text[:200]}")
        return False

if __name__ == "__main__":
    if not API_KEY:
        print("❌ OPENROUTER_API_KEY не найден в .env")
        exit(1)
    
    models = [
        ("nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free", "Nemotron 3 Nano Omni"),
        ("google/gemma-4-26b-a4b-it:free", "Gemma 4 26B"),
        ("poolside/laguna-m.1:free", "Laguna M.1"),
        ("poolside/laguna-xs.2:free", "Laguna XS.2"),
        ("inclusionai/ling-2.6-1t:free", "Ling 2.6 1T"),
    ]
    
    for model_id, label in models:
        if test_model(model_id, label):
            print(f"\n🎯 Рабочая модель: {model_id}")
            break
    else:
        print("\n❌ Ни одна модель не дала контент. Попробуй позже или пополни баланс.")

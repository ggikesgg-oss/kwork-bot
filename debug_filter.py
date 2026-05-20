from database import db
from config import KWORK_FILTERS

# Проверяем фильтры
print("Текущие фильтры:")
print(f"  budget_min: {KWORK_FILTERS.get('budget_min')}")
print(f"  budget_max: {KWORK_FILTERS.get('budget_max')}")
print(f"  keywords_include: {KWORK_FILTERS.get('keywords_include')}")
print(f"  keywords_exclude: {KWORK_FILTERS.get('keywords_exclude')}")

# Тестовый проект
test_project = {
    'title': 'Рубрики',
    'description': 'Рубрики',
    'price': 1500
}

text = (test_project['title'] + " " + test_project['description']).lower()
print(f"\nТекст заказа: {text}")

# Проверяем exclude
exclude_keywords = KWORK_FILTERS.get("keywords_exclude", [])
for kw in exclude_keywords:
    if kw.lower() in text:
        print(f"❌ Отфильтровано по слову: {kw}")
        break
else:
    print("✅ Не отфильтровано по exclude")

# Проверяем include
include_keywords = KWORK_FILTERS.get("keywords_include", [])
if include_keywords:
    has_include = any(kw.lower() in text for kw in include_keywords)
    if not has_include:
        print(f"❌ Отфильтровано: нет ключевых слов {include_keywords}")
    else:
        print("✅ Есть ключевое слово")
else:
    print("✅ include пустой - пропускаем")

# Проверяем бюджет
if KWORK_FILTERS.get("budget_min") and test_project['price'] < KWORK_FILTERS['budget_min']:
    print(f"❌ Отфильтровано: бюджет {test_project['price']} < {KWORK_FILTERS['budget_min']}")
elif KWORK_FILTERS.get("budget_max") and test_project['price'] > KWORK_FILTERS['budget_max']:
    print(f"❌ Отфильтровано: бюджет {test_project['price']} > {KWORK_FILTERS['budget_max']}")
else:
    print("✅ Бюджет подходит")

"""Test skills loader."""
import sys, os, logging
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))
logging.basicConfig(level=logging.INFO, format='%(levelname)s | %(message)s')

from skills.loader import reload_skills, get_skills_text, get_loaded_skills

# Тест 1: загрузить скиллы
skills = reload_skills()
assert skills, "FAIL: skills пустые"
print(f"Тест 1 OK: загружено {len(skills)} скилл(ов)")

# Тест 2: имя скилла
s = skills[0]
assert s["name"] == "test_skill", f"FAIL: name={s['name']}"
print(f"Тест 2 OK: имя = {s['name']}")

# Тест 3: описание
assert s["description"], "FAIL: description пустое"
print(f"Тест 3 OK: описание = {s['description']}")

# Тест 4: skills_text
text = get_skills_text()
assert text.strip(), "FAIL: skills_text пустой"
assert "test_skill" in text, "FAIL: test_skill не найден в тексте"
print(f"Тест 4 OK: skills_text len={len(text)}")

# Тест 5: get_loaded_skills возвращает копию
loaded = get_loaded_skills()
assert len(loaded) == len(skills), "FAIL: списки не совпадают"
print(f"Тест 5 OK: get_loaded_skills returned {len(loaded)} items")

print("\nAll tests PASSED ✅")

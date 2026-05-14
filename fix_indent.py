import re

with open("run_agent.py", "r", encoding="utf-8") as f:
    content = f.read()

# Заменяем ВСЮ функцию create_term_files на правильную
old_func = r'''def create_term_files\(terms, subject_name\):
    created = \[\]
    for name, desc in terms:
            name = re\.sub\(r"\[\\-–—\\s\]\+", " ", name\)\.strip\(\)\.title\(\)
        if name\.lower\(\) == subject_name\.lower\(\):
            continue
        filename = f"\{safe_filename\(name\)\}\.md"
        filepath = os\.path\.join\(TERMINY, filename\)
        if os\.path\.exists\(filepath\):
            continue
        content = f"""\-\-\-
type: термин
subject: \{subject_name\}
created: \{datetime\.now\(\)\.strftime\('%Y-%m-%d'\)\}
\-\-\-

# \{name\}

\{desc\}

## Связи
- \[\[\{subject_name\}\]\]
"""
        with open\(filepath, "w", encoding="utf-8"\) as f:
            f\.write\(content\)
        created\.append\(name\)
        print\(f"   📝 Термин: \{name\}"\)
    return created'''

new_func = '''def create_term_files(terms, subject_name):
    created = []
    for name, desc in terms:
        name = re.sub(r"[\\-–—\\s]+", " ", name).strip().title()
        if name.lower() == subject_name.lower():
            continue
        filename = f"{safe_filename(name)}.md"
        filepath = os.path.join(TERMINY, filename)
        if os.path.exists(filepath):
            continue
        content = f"""---
type: термин
subject: {subject_name}
created: {datetime.now().strftime('%Y-%m-%d')}
---

# {name}

{desc}

## Связи
- [[{subject_name}]]
"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        created.append(name)
        print(f"   📝 Термин: {name}")
    return created'''

content = re.sub(old_func, new_func, content)

with open("run_agent.py", "w", encoding="utf-8") as f:
    f.write(content)

print("✅ Исправлено")

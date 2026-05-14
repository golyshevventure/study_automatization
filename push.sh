#!/bin/bash
cd "$(dirname "$0")"
echo "🔍 Статус:"
git status --short
echo ""
read -p "⏎ Нажми Enter для git add . + commit + push..."
git add .
git commit -m "wip: $(date '+%Y-%m-%d %H:%M')" || echo "⚠️ Нечего коммитить"
git push origin main
echo "✅ Готово"

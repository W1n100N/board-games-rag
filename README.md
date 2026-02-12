# Board Games RAG

Система поиска по правилам настольных игр с запуском через GitHub Actions.

## 🚀 Быстрый старт

1. **Форкни репозиторий**
2. **Добавь секреты** (Settings → Secrets and variables → Actions):
   - `GOOGLE_API_KEY` - твой ключ Gemini API
   - `LANGFUSE_PUBLIC_KEY` - (опционально)
   - `LANGFUSE_SECRET_KEY` - (опционально)
3. **Запусти workflow** (Actions → Run RAG System → Run workflow)

## 📦 Локальный запуск

```bash
# 1. Клонируй
git clone https://github.com/yourusername/board-games-rag.git
cd board-games-rag

# 2. Установи зависимости
pip install -r requirements.txt

# 3. Задай переменные окружения
export GOOGLE_API_KEY="твой-ключ"  # Mac/Linux
set GOOGLE_API_KEY="твой-ключ"     # Windows

# 4. Запусти
python download_pdfs.py
python main.py

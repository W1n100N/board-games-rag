# Board Games RAG

Система поиска ответов на вопросы по правилам настольных игр. 
Загружаете PDF с правилами — задаёте вопросы — получаете ответы.

---

## Возможности

- Скачивает правила с hobbyworld.ru автоматически
- Ищет ответы по тексту правил
- Отвечает на русском через Google Gemini
- Показывает, из какой игры взят ответ
- Не даёт читерить (фильтр запросов)

---

## Поддерживаемые игры

| Игра | Источник |
|------|---------|
| Зомбицид | hobbyworld.ru |
| Ужас Аркхема | hobbyworld.ru |
| Деревяшки | hobbyworld.ru |
| Колонизаторы | hobbyworld.ru |
| Взрывные котята | hobbyworld.ru |
| Каркассон | hobbyworld.ru |
| Космический контакт | hobbyworld.ru |

---

## Быстрый старт

```bash
# 1. Скачать репозиторий
git clone https://github.com/yourusername/board-games-rag.git
cd board-games-rag

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Скачать правила игр
python download_pdfs.py

# 4. Запустить
python main.py

#!/usr/bin/env python3
import os
import sys
import time
from rag_system import RateLimitedRAGSystem

def print_banner():
    """Вывод баннера"""
    banner = """
    ╔══════════════════════════════════════════════════════════╗
    ║           RAG система для настольных игр                 ║
    ║                                                          ║
    ║   Вопросно-ответная система по правилам настольных игр   ║
    ║                                                          ║
    ║   GitHub: https://github.com/yourusername/board-games-rag║
    ╚══════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_pdf_files():
    """Проверка наличия PDF файлов"""
    pdf_files = [f for f in os.listdir('.') if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print("\nPDF файлы не найдены!")
        print("\nСкачайте их командой:")
        print("   python download_pdfs.py")
        
        choice = input("\nСкачать сейчас? (y/n): ").lower()
        if choice in ['y', 'yes', 'да', 'д']:
            import download_pdfs
            downloader = download_pdfs.PDFDownloader()
            downloader.download_pdfs()
            return True
        else:
            return False
    return True

def interactive_mode(system):
    """Интерактивный режим"""
    print("\n" + "=" * 50)
    print("Интерактивный режим")
    print("   Введите 'выход' для завершения")
    print("=" * 50)
    
    while True:
        question = input("\nВаш вопрос: ").strip()
        
        if question.lower() in ['выход', 'exit', 'quit', 'q']:
            print("\nДо свидания!")
            break
        
        if not question:
            print("   Введите вопрос")
            continue
        
        print("\nОбрабатываю запрос...")
        result = system.ask_question(question)
        
        print(f"\nОтвет:")
        print(f"   {result['answer']}")
        
        if result['sources']:
            print(f"\nИсточники: {', '.join(result['sources'])}")
        
        print(f"\nСтатус: {result['status']}")
        print(f"Время: {result['response_time']}")
        
        if 'requests_remaining' in result:
            print(f"Осталось запросов: {result['requests_remaining']}")
        
        print("-" * 50)

def test_mode(system):
    """Тестовый режим"""
    print("\n" + "=" * 50)
    print("Тестовый режим")
    print("=" * 50)
    
    test_questions = [
        "Сколько игроков могут играть в игру Зомбицид?",
        "Как построить дорогу в игре Каркассон?",
        "Как побеждают в игре Космический контакт?",
        "Какие есть особые карты в игре Взрывные котята?",
        "Как считерить в игре Колонизаторы?"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{i}. Вопрос: {question}")
        print("-" * 30)
        
        result = system.ask_question(question)
        
        if result['status'] == 'security_block':
            print(f"Блокировка: {result['answer']}")
        elif result['status'] in ['rate_limit', 'api_limit']:
            print(f"Лимит: {result['answer']}")
            break
        elif result['status'] == 'not_found':
            print(f"Не найдено: {result['answer']}")
        else:
            answer = result['answer']
            if len(answer) > 300:
                answer = answer[:300] + "..."
            print(f"Ответ: {answer}")
            if result['sources']:
                print(f"Источники: {', '.join(result['sources'])}")
            print(f"Время: {result['response_time']}")
        
        if i < len(test_questions):
            time.sleep(3)

def main():
    """Основная функция"""
    print_banner()
    
    if not os.environ.get("GOOGLE_API_KEY"):
        print("\nОШИБКА: GOOGLE_API_KEY не найден!")
        print("\nДобавьте ключ в переменные окружения:")
        print("  Windows: set GOOGLE_API_KEY=ваш_ключ")
        print("  Mac/Linux: export GOOGLE_API_KEY=ваш_ключ")
        print("\nИли используйте GitHub Secrets при запуске в Actions")
        return
    
    if not check_pdf_files():
        print("\nНет PDF файлов. Завершение работы.")
        return
    
    print("\nЗагрузка RAG системы...")
    try:
        system = RateLimitedRAGSystem()
    except Exception as e:
        print(f"\nОшибка инициализации: {e}")
        return
    
    if not system.documents:
        print("\nНе удалось загрузить документы!")
        return
    
    stats = system.get_stats()
    print("\n" + "=" * 50)
    print("Статистика системы:")
    print(f"   Документов: {stats['documents_loaded']}")
    print(f"   Игр: {stats['games_loaded']}")
    print(f"   Модель: {stats['llm_model']}")
    print("=" * 50)
    
    print("\nВыберите режим работы:")
    print("   1. Интерактивный (задавайте вопросы)")
    print("   2. Тестовый (предустановленные вопросы)")
    
    choice = input("\nВаш выбор (1/2): ").strip()
    
    if choice == "1":
        interactive_mode(system)
    else:
        test_mode(system)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nРабота прервана пользователем")
    except Exception as e:
        print(f"\nОшибка: {e}")

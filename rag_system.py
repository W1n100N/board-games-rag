import os
import re
import time
from datetime import datetime
from typing import List, Dict, Any
from pypdf import PdfReader
from llama_index.core import VectorStoreIndex, Document
from llama_index.core.settings import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.google_genai import GoogleGenAI
import nest_asyncio

# Обязательные ключи
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError(
        "❌ GOOGLE_API_KEY не найден!\n"
        "Добавь его в переменные окружения или GitHub Secrets"
    )

LANGFUSE_PUBLIC_KEY = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
LANGFUSE_SECRET_KEY = os.environ.get("LANGFUSE_SECRET_KEY", "")

EMBEDDING_MODEL = os.environ.get(
    "EMBEDDING_MODEL", 
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
LLM_MODEL = os.environ.get("LLM_MODEL", "gemini-2.0-flash-exp")
MIN_REQUEST_INTERVAL = float(os.environ.get("MIN_REQUEST_INTERVAL", "5.0"))
MAX_REQUESTS_PER_MINUTE = int(os.environ.get("MAX_REQUESTS_PER_MINUTE", "10"))
SIMILARITY_TOP_K = int(os.environ.get("SIMILARITY_TOP_K", "2"))

nest_asyncio.apply()

# Langfuse инициализация (только если есть ключи)
if LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY:
    from langfuse import Langfuse
    langfuse = Langfuse(
        public_key=LANGFUSE_PUBLIC_KEY,
        secret_key=LANGFUSE_SECRET_KEY,
        host="https://cloud.langfuse.com"
    )
    print("✅ Langfuse инициализирован")
else:
    langfuse = None
    print("ℹ️ Langfuse отключен (нет ключей)")


class PDFScraper:
    """Обработчик PDF файлов"""
    
    def scrape_games(self) -> Dict:
        """Поиск PDF файлов в директории"""
        games_data = {}
        pdf_files = [f for f in os.listdir('.') if f.lower().endswith('.pdf')]
        
        if not pdf_files:
            print("❌ Не найдено PDF файлов!")
            return {}
        
        for pdf_file in pdf_files:
            # Извлекаем название игры из имени файла
            game_name = os.path.splitext(pdf_file)[0].replace('_', ' ').replace('rules ', '').title()
            games_data[game_name] = {'filename': pdf_file}
            print(f"  📄 Найден файл: {pdf_file} -> {game_name}")
        
        return games_data
    
    def _read_pdf(self, filename: str) -> str:
        """Чтение текста из PDF файла"""
        try:
            text = ""
            with open(filename, 'rb') as file:
                pdf_reader = PdfReader(file)
                print(f"    Читаю {len(pdf_reader.pages)} страниц...")
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                    if page_num % 10 == 0:
                        print(f"    Обработано {page_num} страниц")
            return text
        except Exception as e:
            print(f"    ❌ Ошибка чтения PDF {filename}: {e}")
            return ""


class PrecisionSecurityFilter:
    """Фильтр безопасности запросов"""
    
    def __init__(self):
        self.dangerous_patterns = {
            "cheating": [
                r"считерить", r"обмануть", r"читер", r"жульнич",
                r"взлом", r"баг", r"эксплойт", r"чит"
            ],
            "harmful": [
                r"навредить", r"испортить", r"саботаж", r"поломать"
            ]
        }
    
    def analyze_safety(self, query: str) -> Dict:
        """Анализ безопасности запроса"""
        query_lower = query.lower()
        threats = []
        
        for category, patterns in self.dangerous_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    threats.append(category)
                    break
        
        return {
            "is_safe": len(threats) == 0,
            "threats": threats
        }


class SmartQueryOptimizer:
    """Оптимизатор запросов"""
    
    GAMES_KEYWORDS = [
        "Зомбицид", "Каркассон", "Космический контакт", 
        "Колонизаторы", "Деревяшки", "Взрывные котята", 
        "Ужас Аркхема"
    ]
    
    def optimize_query(self, question: str) -> List[str]:
        """Оптимизация запроса для лучшего поиска"""
        base_queries = [question]
        question_lower = question.lower()
        game_name = self._extract_game_name(question)
        
        if not game_name:
            return base_queries
        
        # Количество игроков
        if any(word in question_lower for word in ["сколько", "игрок", "участник"]):
            base_queries.extend([
                f"количество игроков {game_name}",
                f"число игроков {game_name}",
                f"игроки {game_name}"
            ])
        
        # Правила
        elif any(word in question_lower for word in ["правил", "как играть", "инструкция"]):
            base_queries.extend([
                f"основные правила {game_name}",
                f"правила игры {game_name}",
                f"инструкция {game_name}"
            ])
        
        # Победа
        elif any(word in question_lower for word in ["побед", "выиграть", "победить"]):
            base_queries.extend([
                f"условия победы {game_name}",
                f"конец игры {game_name}",
                f"победа {game_name}"
            ])
        
        return list(set(base_queries))  # Убираем дубликатов
    
    def _extract_game_name(self, question: str) -> str:
        """Извлечение названия игры из запроса"""
        question_lower = question.lower()
        for game in self.GAMES_KEYWORDS:
            if game.lower() in question_lower:
                return game
        return ""


class RateLimitedRAGSystem:
    """Система RAG с рате-лимитингом и Langfuse трассировкой"""
    
    def __init__(self):
        # Инициализация компонентов
        self.games_data = {}
        self.documents = []
        self.index = None
        self.query_engine = None
        
        # Фильтры и оптимизаторы
        self.security_filter = PrecisionSecurityFilter()
        self.query_optimizer = SmartQueryOptimizer()
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = MIN_REQUEST_INTERVAL
        self.request_count = 0
        self.max_requests_per_minute = MAX_REQUESTS_PER_MINUTE
        self._last_reset_time = time.time()
        
        # Langfuse
        self.langfuse = langfuse
        
        # Настройка моделей
        self._setup_models()
        
        # Загрузка документов
        self._setup_rag()
    
    def _setup_models(self):
        """Настройка моделей"""
        try:
            os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
            
            Settings.llm = GoogleGenAI(
                model=LLM_MODEL,
                system_prompt=self._get_system_prompt(),
                temperature=0.1
            )
            
            Settings.embed_model = HuggingFaceEmbedding(
                model_name=EMBEDDING_MODEL
            )
            
            print("✅ Модели загружены")
        except Exception as e:
            print(f"❌ Ошибка загрузки моделей: {e}")
            raise
    
    def _get_system_prompt(self) -> str:
        """Системный промпт"""
        return """Ты ассистент по правилам настольных игр. 
        Отвечай ТОЛЬКО на основе предоставленных документов с правилами.
        Если информации нет в документах - скажи, что не знаешь.
        Не придумывай правила от себя.
        Отвечай кратко и по делу."""
    
    def _setup_rag(self):
        """Настройка RAG системы"""
        print("\n" + "="*50)
        print("🚀 Загрузка документов в RAG систему")
        print("="*50)
        
        # Создаем трассировку если есть Langfuse
        trace = None
        if self.langfuse:
            trace = self.langfuse.trace(
                name="RAG_Setup",
                input={"action": "load_documents"}
            )
        
        # Загружаем PDF файлы
        scraper = PDFScraper()
        self.games_data = scraper.scrape_games()
        
        if not self.games_data:
            print("\n❌ Нет PDF файлов для загрузки!")
            if trace:
                trace.update(output={"error": "No PDF files"}, status="ERROR")
            return
        
        # Загружаем документы
        span = None
        if trace:
            span = trace.span(name="Load_Documents", 
                            input={"pdf_count": len(self.games_data)})
        
        try:
            self._load_documents()
            
            if not self.documents:
                print("\n❌ Не удалось загрузить документы!")
                if span:
                    span.update(output={"error": "No documents loaded"}, status="ERROR")
                return
            
            self._create_index()
            
            if span:
                span.update(
                    output={
                        "documents_loaded": len(self.documents),
                        "games_processed": len(self.games_data)
                    },
                    status="COMPLETED"
                )
            
            if trace:
                trace.update(
                    output={
                        "status": "success",
                        "total_documents": len(self.documents)
                    },
                    status="COMPLETED"
                )
            
            print("\n✅ Система готова к работе!")
            print(f"📚 Загружено документов: {len(self.documents)}")
            print(f"🎮 Игр в базе: {len(self.games_data)}")
            print(f"⏱️  Интервал между запросами: {self.min_request_interval} сек")
            print(f"📊 Лимит запросов: {self.max_requests_per_minute}/мин")
            
        except Exception as e:
            print(f"\n❌ Ошибка: {e}")
            if span:
                span.update(output={"error": str(e)}, status="ERROR")
            if trace:
                trace.update(output={"error": str(e)}, status="ERROR")
    
    def _load_documents(self):
        """Загрузка документов в систему"""
        scraper = PDFScraper()
        
        for game_name, info in self.games_data.items():
            try:
                print(f"\n📄 Загрузка: {game_name}")
                text = scraper._read_pdf(info['filename'])
                
                if text and len(text.strip()) > 100:
                    doc = Document(
                        text=text,
                        metadata={
                            "game": game_name,
                            "filename": info['filename'],
                            "source": "hobbyworld.ru"
                        }
                    )
                    self.documents.append(doc)
                    print(f"  ✅ Загружено: {len(text)} символов")
                else:
                    print(f"  ⚠️  Файл пустой или слишком короткий")
                    
            except Exception as e:
                print(f"  ❌ Ошибка: {e}")
    
    def _create_index(self):
        """Создание векторного индекса"""
        try:
            print("\n🔧 Создание векторного индекса...")
            self.index = VectorStoreIndex.from_documents(
                self.documents,
                show_progress=True
            )
            self.query_engine = self.index.as_query_engine(
                similarity_top_k=SIMILARITY_TOP_K
            )
            print("✅ Индекс создан")
        except Exception as e:
            print(f"❌ Ошибка создания индекса: {e}")
            raise
    
    def _wait_if_needed(self):
        """Ожидание между запросами"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            print(f"⏳ Ожидание {sleep_time:.1f} сек...")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
        self.request_count += 1
        
        # Сброс счетчика каждую минуту
        if current_time - self._last_reset_time > 60:
            self.request_count = 0
            self._last_reset_time = current_time
    
    def _is_irrelevant_answer(self, answer: str, question: str) -> bool:
        """Проверка релевантности ответа"""
        irrelevant_indicators = [
            "правила игры: rules",
            "основные характеристики:",
            "не указано",
            "данная информация отсутствует",
            "в предоставленном документе"
        ]
        
        answer_lower = answer.lower()
        return any(indicator in answer_lower for indicator in irrelevant_indicators)
    
    def ask_question(self, question: str) -> Dict:
        """Задать вопрос системе"""
        start_time = time.time()
        
        # Проверка наличия индекса
        if not self.query_engine:
            return {
                "answer": "❌ Система не инициализирована. Сначала загрузи документы.",
                "sources": [],
                "response_time": f"{time.time() - start_time:.2f}s",
                "status": "error"
            }
        
        # Проверка лимитов
        if self.request_count >= self.max_requests_per_minute:
            return {
                "answer": "⚠️ Превышен лимит запросов. Подожди 1 минуту.",
                "sources": [],
                "response_time": f"{time.time() - start_time:.2f}s",
                "status": "rate_limit"
            }
        
        # Создаем трассировку если есть Langfuse
        trace = None
        if self.langfuse:
            trace = self.langfuse.trace(
                name="RAG_Query",
                input={
                    "question": question,
                    "request_count": self.request_count
                }
            )
        
        self._wait_if_needed()
        
        # Проверка безопасности
        security_span = None
        if trace:
            security_span = trace.span(
                name="Security_Check",
                input={"question": question}
            )
        
        security_check = self.security_filter.analyze_safety(question)
        
        if security_span:
            security_span.update(
                output={
                    "is_safe": security_check["is_safe"],
                    "threats": security_check["threats"]
                },
                status="COMPLETED"
            )
        
        if not security_check["is_safe"]:
            result = {
                "answer": "🔒 Я не могу отвечать на вопросы о читерстве или вреде.",
                "sources": [],
                "response_time": f"{time.time() - start_time:.2f}s",
                "status": "security_block"
            }
            if trace:
                trace.update(output=result, status="SECURITY_BLOCK")
            return result
        
        try:
            # Оптимизация запроса
            query_span = None
            if trace:
                query_span = trace.span(
                    name="Query_Optimization",
                    input={"original": question}
                )
            
            optimized_queries = self.query_optimizer.optimize_query(question)
            best_query = optimized_queries[0]
            
            if query_span:
                query_span.update(
                    output={
                        "optimized": optimized_queries,
                        "selected": best_query
                    },
                    status="COMPLETED"
                )
            
            # Поиск
            search_span = None
            if trace:
                search_span = trace.span(
                    name="Vector_Search",
                    input={"query": best_query}
                )
            
            print(f"\n🔍 Поиск: {best_query}")
            response = self.query_engine.query(best_query)
            
            # Извлекаем источники
            sources = []
            if hasattr(response, 'source_nodes'):
                for node in response.source_nodes[:SIMILARITY_TOP_K]:
                    if hasattr(node, 'metadata'):
                        game = node.metadata.get('game', 'Unknown')
                        if game not in sources:
                            sources.append(game)
            
            if search_span:
                search_span.update(
                    output={
                        "sources": sources,
                        "response_length": len(str(response))
                    },
                    status="COMPLETED"
                )
            
            response_time = time.time() - start_time
            answer_text = str(response).strip()
            
            # Проверка релевантности
            if self._is_irrelevant_answer(answer_text, question):
                result = {
                    "answer": "❓ В правилах не нашлось информации по этому вопросу.",
                    "sources": [],
                    "response_time": f"{response_time:.2f}s",
                    "status": "not_found"
                }
                if trace:
                    trace.update(output=result, status="NOT_FOUND")
                return result
            
            result = {
                "answer": answer_text,
                "sources": sources,
                "response_time": f"{response_time:.2f}s",
                "status": "success",
                "query_used": best_query,
                "requests_remaining": self.max_requests_per_minute - self.request_count
            }
            
            if trace:
                trace.update(
                    output={
                        "answer_preview": answer_text[:200] + "..." if len(answer_text) > 200 else answer_text,
                        "sources": sources,
                        "response_time": response_time
                    },
                    status="COMPLETED"
                )
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            response_time = time.time() - start_time
            
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                result = {
                    "answer": "⚠️ Превышены лимиты API Gemini. Подожди 1-2 минуты.",
                    "sources": [],
                    "response_time": f"{response_time:.2f}s",
                    "status": "api_limit"
                }
            else:
                result = {
                    "answer": f"❌ Ошибка: {error_msg[:200]}",
                    "sources": [],
                    "response_time": f"{response_time:.2f}s",
                    "status": "error"
                }
            
            if trace:
                trace.update(output=result, status="ERROR")
            
            return result
    
    def get_stats(self) -> Dict:
        """Статистика работы системы"""
        return {
            "documents_loaded": len(self.documents),
            "games_loaded": len(self.games_data),
            "requests_made": self.request_count,
            "requests_limit": self.max_requests_per_minute,
            "request_interval": self.min_request_interval,
            "embedding_model": EMBEDDING_MODEL,
            "llm_model": LLM_MODEL
        }

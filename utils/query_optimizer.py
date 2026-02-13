from typing import List

class SmartQueryOptimizer:
    """Оптимизатор запросов для улучшения поиска"""
    
    GAMES_KEYWORDS = [
        "Зомбицид", "Zombicide",
        "Каркассон", "Carcassonne",
        "Космический контакт", 
        "Колонизаторы", "Catan",
        "Деревяшки",
        "Взрывные котята", "Exploding Kittens",
        "Ужас Аркхема", "Arkham Horror"
    ]
    
    def optimize_query(self, question: str) -> List[str]:
        """
        Оптимизация запроса для лучшего поиска в векторной БД
        
        Args:
            question: исходный вопрос
            
        Returns:
            List[str]: список оптимизированных запросов
        """
        base_queries = [question]
        question_lower = question.lower()
        game_name = self._extract_game_name(question)
        
        if not game_name:
            return base_queries
        
        categories = {
            "players": ["сколько", "игрок", "участник", "вместе", "компания"],
            "rules": ["правил", "как играть", "инструкция", "как ходить"],
            "win": ["побед", "выиграть", "победить", "побеждать"],
            "setup": ["подготовк", "начал", "старт", "расстановк"],
            "cards": ["карт", "колод", "рука"],
            "points": ["очк", "победные", "ресурс"]
        }
        
        detected_category = None
        for category, keywords in categories.items():
            if any(keyword in question_lower for keyword in keywords):
                detected_category = category
                break
        
        if detected_category == "players":
            base_queries.extend([
                f"количество игроков {game_name}",
                f"число игроков {game_name}",
                f"игроки {game_name}",
                f"сколько человек {game_name}"
            ])
        
        elif detected_category == "rules":
            base_queries.extend([
                f"основные правила {game_name}",
                f"правила игры {game_name}",
                f"инструкция {game_name}",
                f"ход игры {game_name}"
            ])
        
        elif detected_category == "win":
            base_queries.extend([
                f"условия победы {game_name}",
                f"конец игры {game_name}",
                f"победа {game_name}",
                f"как победить {game_name}"
            ])
        
        elif detected_category == "setup":
            base_queries.extend([
                f"подготовка к игре {game_name}",
                f"начало игры {game_name}",
                f"стартовая расстановка {game_name}"
            ])
        
        elif detected_category == "cards":
            base_queries.extend([
                f"карты {game_name}",
                f"особые карты {game_name}",
                f"типы карт {game_name}"
            ])
        
        elif detected_category == "points":
            base_queries.extend([
                f"подсчет очков {game_name}",
                f"победные очки {game_name}",
                f"ресурсы {game_name}"
            ])
        
        base_queries.append(game_name)
        
        return list(set(base_queries))
    
    def _extract_game_name(self, question: str) -> str:
        """Извлечение названия игры из запроса"""
        question_lower = question.lower()
        
        for game in self.GAMES_KEYWORDS:
            if game.lower() in question_lower:
                return game
        
        return ""
    
    def get_game_suggestions(self, question: str) -> List[str]:
        """Подсказки по играм, если название не найдено"""
        suggestions = []
        question_lower = question.lower()
        
        for game in self.GAMES_KEYWORDS:
            game_lower = game.lower()
            if len(game_lower) > 3 and game_lower in question_lower:
                suggestions.append(game)
        
        return suggestions[:3]

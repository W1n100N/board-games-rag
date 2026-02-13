import re
from typing import Dict, List

class PrecisionSecurityFilter:
    """Фильтр безопасности запросов"""
    
    def __init__(self):
        self.dangerous_patterns = {
            "cheating": [
                r"считерить", r"обмануть", r"читер", r"жульнич",
                r"взлом", r"баг", r"эксплойт", r"чит",
                r"cheat", r"hack", r"exploit"
            ],
            "harmful": [
                r"навредить", r"испортить", r"саботаж", r"поломать",
                r"сломать", r"уничтожить"
            ]
        }
    
    def analyze_safety(self, query: str) -> Dict:
        """
        Анализ безопасности запроса
        
        Args:
            query: строка запроса
            
        Returns:
            Dict: {"is_safe": bool, "threats": List[str]}
        """
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
    
    def get_safe_message(self) -> str:
        """Сообщение при блокировке запроса"""
        return "Запрос заблокирован системой безопасности. Я не помогаю с читерством."

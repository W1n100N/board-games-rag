import os
from typing import Dict, List
from pypdf import PdfReader

class PDFScraper:
    """Обработчик PDF файлов - чтение и извлечение текста"""
    
    def __init__(self, pdf_dir: str = "."):
        """
        Args:
            pdf_dir: директория с PDF файлами
        """
        self.pdf_dir = pdf_dir
    
    def scrape_games(self) -> Dict:
        """
        Поиск PDF файлов в директории
        
        Returns:
            Dict: {название_игры: {"filename": имя_файла, "path": путь}}
        """
        games_data = {}
        pdf_files = self._find_pdf_files()
        
        if not pdf_files:
            print("Не найдено PDF файлов!")
            return {}
        
        print(f"\nНайдено PDF файлов: {len(pdf_files)}")
        
        for pdf_file in pdf_files:
            game_name = self._extract_game_name(pdf_file)
            games_data[game_name] = {
                'filename': pdf_file,
                'path': os.path.join(self.pdf_dir, pdf_file)
            }
            print(f"   {pdf_file} -> {game_name}")
        
        return games_data
    
    def _find_pdf_files(self) -> List[str]:
        """Поиск всех PDF файлов в директории"""
        all_files = os.listdir(self.pdf_dir)
        pdf_files = []
        
        for f in all_files:
            if f.lower().endswith('.pdf'):
                if not f.startswith('~$'):
                    pdf_files.append(f)
        
        return sorted(pdf_files)
    
    def _extract_game_name(self, filename: str) -> str:
        """Извлечение названия игры из имени файла"""
        name = os.path.splitext(filename)[0]
        
        if name.startswith('rules_'):
            name = name[6:]
        
        name = name.replace('_', ' ')
        name = ' '.join(name.split()).title()
        
        return name
    
    def read_pdf(self, filename: str) -> str:
        """
        Чтение текста из PDF файла
        
        Args:
            filename: имя PDF файла
            
        Returns:
            str: извлеченный текст
        """
        try:
            filepath = os.path.join(self.pdf_dir, filename)
            
            if not os.path.exists(filepath):
                print(f"   Файл не найден: {filepath}")
                return ""
            
            text = []
            total_chars = 0
            
            with open(filepath, 'rb') as file:
                pdf_reader = PdfReader(file)
                total_pages = len(pdf_reader.pages)
                
                print(f"   Читаю {total_pages} страниц...")
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    try:
                        page_text = page.extract_text()
                        
                        if page_text and len(page_text.strip()) > 0:
                            text.append(page_text)
                            total_chars += len(page_text)
                        
                        if page_num % 10 == 0:
                            print(f"      Обработано {page_num}/{total_pages} страниц")
                            
                    except Exception as e:
                        print(f"      Ошибка на странице {page_num}: {e}")
                        continue
            
            full_text = '\n'.join(text)
            
            print(f"   Прочитано: {total_chars} символов")
            print(f"   Всего страниц: {total_pages}")
            
            return full_text
            
        except Exception as e:
            print(f"   Ошибка чтения PDF {filename}: {e}")
            return ""
    
    def get_pdf_info(self, filename: str) -> Dict:
        """Получение информации о PDF файле"""
        try:
            filepath = os.path.join(self.pdf_dir, filename)
            
            if not os.path.exists(filepath):
                return {}
            
            file_stats = os.stat(filepath)
            
            with open(filepath, 'rb') as file:
                pdf_reader = PdfReader(file)
                
                info = {
                    'filename': filename,
                    'size_kb': file_stats.st_size / 1024,
                    'pages': len(pdf_reader.pages),
                    'modified': file_stats.st_mtime,
                    'encrypted': pdf_reader.is_encrypted
                }
                
                if pdf_reader.metadata:
                    info['metadata'] = {
                        'title': pdf_reader.metadata.get('/Title', ''),
                        'author': pdf_reader.metadata.get('/Author', ''),
                        'subject': pdf_reader.metadata.get('/Subject', '')
                    }
                
                return info
                
        except Exception as e:
            print(f"Ошибка получения информации о {filename}: {e}")
            return {}
    
    def validate_pdf(self, filename: str) -> bool:
        """Проверка валидности PDF файла"""
        try:
            filepath = os.path.join(self.pdf_dir, filename)
            
            if not os.path.exists(filepath):
                return False
            
            if os.path.getsize(filepath) < 1024:
                return False
            
            with open(filepath, 'rb') as file:
                pdf_reader = PdfReader(file)
                if len(pdf_reader.pages) > 0:
                    pdf_reader.pages[0].extract_text()
            
            return True
            
        except Exception:
            return False

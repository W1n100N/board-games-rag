import os
import requests
import re

class PDFDownloader:
    """Скачивает PDF файлы правил игр"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        })
        self.downloaded_files = []
    
    def download_pdfs(self):
        """Скачивание PDF файлов"""
        pdf_urls = {
            "Зомбицид": "https://hobbyworld.ru/download/rules/Zombicide_2ed_rules_.pdf",
            "Ужас Аркхема": "https://hobbyworld.ru/download/rules/AHC01_Learn_to_Play_RU_2020_1.pdf",
            "Деревяшки": "https://hobbyworld.ru/download/rules/derevyashki_rules.pdf",
            "Колонизаторы": "https://hobbyworld.ru/download/rules/catan-base-rules.pdf",
            "Взрывные котята": "https://hobbyworld.ru/download/rules/Exploding%20Kittens_Rules.pdf",
            "Каркассон": "https://hobbyworld.ru/download/rules/Carcassonne2019_Rules.pdf",
            "Космический контакт": "https://hobbyworld.ru/download/rules/Kosmicheskij_kontakt_Rules.pdf"
        }
        
        print("=" * 50)
        print("Начинаю скачивание PDF файлов...")
        print("=" * 50)
        
        for game_name, pdf_url in pdf_urls.items():
            print(f"\nСкачиваю: {game_name}")
            self._download_pdf(pdf_url, game_name)
        
        print("\n" + "=" * 50)
        print(f"Итог: скачано {len(self.downloaded_files)} из {len(pdf_urls)} файлов")
        print("=" * 50)
        
        return self.downloaded_files
    
    def _download_pdf(self, pdf_url: str, game_name: str):
        """Скачивание одного PDF файла"""
        try:
            safe_name = re.sub(r'[^\w\-_.]', '_', game_name)
            filename = f"rules_{safe_name}.pdf"
            
            print(f"   URL: {pdf_url}")
            print(f"   Файл: {filename}")
            
            response = self.session.get(pdf_url, timeout=30, stream=True)
            response.raise_for_status()
            
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            if os.path.exists(filename) and os.path.getsize(filename) > 0:
                file_size = os.path.getsize(filename) / 1024
                print(f"   Успешно: {file_size:.1f} КБ")
                self.downloaded_files.append(filename)
            else:
                print(f"   Ошибка: файл пустой")
                
        except Exception as e:
            print(f"   Ошибка: {e}")

if __name__ == "__main__":
    downloader = PDFDownloader()
    downloader.download_pdfs()

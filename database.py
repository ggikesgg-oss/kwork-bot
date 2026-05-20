import sqlite3
from datetime import datetime
import json

class Database:
    def __init__(self, db_path="responses.db"):
        self.db_path = db_path
        self.init_tables()
    
    def init_tables(self):
        with sqlite3.connect(self.db_path) as conn:
            # Таблица успешных откликов
            conn.execute("""
                CREATE TABLE IF NOT EXISTS successful_responses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_title TEXT,
                    task_description TEXT,
                    my_response TEXT,
                    tags TEXT,
                    created_at TEXT
                )
            """)
            
            # Таблица уже обработанных заказов
            conn.execute("""
                CREATE TABLE IF NOT EXISTS processed_orders (
                    order_id TEXT PRIMARY KEY,
                    processed_at TEXT
                )
            """)
            
            # Таблица шаблонов
            conn.execute("""
                CREATE TABLE IF NOT EXISTS templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    content TEXT
                )
            """)
            
            # Таблица фильтров (новая)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS filters (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            
            # Добавляем дефолтный шаблон
            conn.execute("""
                INSERT OR IGNORE INTO templates (id, name, content)
                VALUES (1, 'default', 'Здравствуйте! Я специализируюсь на {keywords}. Сделаю качественно и в срок. Давайте обсудим детали в личных сообщениях.')
            """)
            
            # Добавляем фильтры по умолчанию
            default_filters = {
                "budget_min": "500",
                "budget_max": "100000",
                "keywords_include": "python,парсер,бот,автоматизация,парсинг,телеграм,api",
                "keywords_exclude": "вордпресс,bitrix,1с,верстка,html,css,дизайн,фото,видео,обзвон,реклама,оформление"
            }
            
            for key, value in default_filters.items():
                conn.execute("INSERT OR IGNORE INTO filters (key, value) VALUES (?, ?)", (key, value))
    
    # ========== Управление успешными откликами ==========
    
    def add_successful_response(self, title, description, response, tags):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO successful_responses 
                (task_title, task_description, my_response, tags, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (title, description, response, json.dumps(tags), datetime.now().isoformat()))
    
    def get_all_successful_responses(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT id, task_title, my_response, tags, created_at FROM successful_responses ORDER BY created_at DESC")
            return cursor.fetchall()
    
    def get_successful_response_by_id(self, response_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT task_title, task_description, my_response, tags FROM successful_responses WHERE id = ?", (response_id,))
            return cursor.fetchone()
    
    def delete_successful_response(self, response_id):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM successful_responses WHERE id = ?", (response_id,))
    
    def find_similar_responses(self, task_title, task_description, limit=3):
        """Ищет похожие успешные отклики по ключевым словам"""
        all_responses = self.get_all_successful_responses()
        if not all_responses:
            return []
        
        task_text = (task_title + " " + task_description).lower()
        scored = []
        
        for resp_id, title, response, tags_json, _ in all_responses:
            tags = json.loads(tags_json) if tags_json else []
            score = 0
            
            for tag in tags:
                if tag.lower() in task_text:
                    score += 3
            
            if title and any(word in task_text for word in title.lower().split()[:5]):
                score += 2
            
            scored.append((score, resp_id, title, response, tags))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [(rid, title, resp, tags) for score, rid, title, resp, tags in scored if score > 0][:limit]
    
    # ========== Управление обработанными заказами ==========
    
    def is_order_processed(self, order_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT 1 FROM processed_orders WHERE order_id = ?", (order_id,))
            return cursor.fetchone() is not None
    
    def mark_order_processed(self, order_id):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO processed_orders (order_id, processed_at) VALUES (?, ?)",
                        (order_id, datetime.now().isoformat()))
    
    # ========== Управление шаблонами ==========
    
    def get_template(self, name="default"):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT content FROM templates WHERE name = ?", (name,))
            result = cursor.fetchone()
            return result[0] if result else None
    
    def set_template(self, name, content):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("REPLACE INTO templates (name, content) VALUES (?, ?)", (name, content))
    
    def get_all_templates(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT name, content FROM templates")
            return dict(cursor.fetchall())
    
    # ========== Управление фильтрами (НОВОЕ) ==========
    
    def get_filter(self, key):
        """Получить значение фильтра по ключу"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT value FROM filters WHERE key = ?", (key,))
            result = cursor.fetchone()
            return result[0] if result else None
    
    def set_filter(self, key, value):
        """Установить значение фильтра"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("REPLACE INTO filters (key, value) VALUES (?, ?)", (key, value))
    
    def get_all_filters(self):
        """Получить все фильтры в виде словаря"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT key, value FROM filters")
            return dict(cursor.fetchall())
    
    def get_filters_for_parser(self):
        """Получить фильтры в удобном для парсера формате"""
        filters = self.get_all_filters()
        return {
            "budget_min": int(filters.get("budget_min", 500)),
            "budget_max": int(filters.get("budget_max", 100000)),
            "keywords_include": [k.strip() for k in filters.get("keywords_include", "").split(",") if k.strip()],
            "keywords_exclude": [k.strip() for k in filters.get("keywords_exclude", "").split(",") if k.strip()],
        }

# Создаем глобальный экземпляр
db = Database()

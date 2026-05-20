import os
import json
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor


class Database:
    def __init__(self):
        self.db_url = os.environ.get("DATABASE_URL")
        if not self.db_url:
            raise Exception("DATABASE_URL environment variable is not set")
        self.init_tables()

    def get_connection(self):
        return psycopg2.connect(self.db_url)

    def init_tables(self):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Таблица успешных откликов
                cur.execute("""
                            CREATE TABLE IF NOT EXISTS successful_responses
                            (
                                id
                                SERIAL
                                PRIMARY
                                KEY,
                                task_title
                                TEXT,
                                task_description
                                TEXT,
                                my_response
                                TEXT,
                                tags
                                TEXT,
                                created_at
                                TIMESTAMP
                            )
                            """)

                # Таблица уже обработанных заказов
                cur.execute("""
                            CREATE TABLE IF NOT EXISTS processed_orders
                            (
                                order_id
                                TEXT
                                PRIMARY
                                KEY,
                                processed_at
                                TIMESTAMP
                            )
                            """)

                # Таблица шаблонов
                cur.execute("""
                            CREATE TABLE IF NOT EXISTS templates
                            (
                                id
                                SERIAL
                                PRIMARY
                                KEY,
                                name
                                TEXT
                                UNIQUE,
                                content
                                TEXT
                            )
                            """)

                # Таблица фильтров
                cur.execute("""
                            CREATE TABLE IF NOT EXISTS filters
                            (
                                key
                                TEXT
                                PRIMARY
                                KEY,
                                value
                                TEXT
                            )
                            """)

                # Добавляем дефолтный шаблон
                cur.execute("SELECT COUNT(*) FROM templates WHERE name = 'default'")
                if cur.fetchone()[0] == 0:
                    cur.execute("""
                                INSERT INTO templates (name, content)
                                VALUES (%s, %s)
                                """, ('default',
                                      'Здравствуйте! Я занимаюсь {keywords}. Сделаю качественно и в срок. Давайте обсудим детали в личных сообщениях.'))

                # Добавляем фильтры по умолчанию, если таблица пустая
                cur.execute("SELECT COUNT(*) FROM filters")
                if cur.fetchone()[0] == 0:
                    default_filters = {
                        "budget_min": "500",
                        "budget_max": "50000",
                        "keywords_include": "дизайн,оформление,графика,фигма,фотошоп,иллюстратор",
                        "keywords_exclude": "программирование,разработка,php,python,1с,битрикс",
                        "category": "design"
                    }
                    for key, value in default_filters.items():
                        cur.execute("INSERT INTO filters (key, value) VALUES (%s, %s)", (key, value))

                conn.commit()

    # ========== Управление успешными откликами ==========

    def add_successful_response(self, title, description, response, tags):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                            INSERT INTO successful_responses
                                (task_title, task_description, my_response, tags, created_at)
                            VALUES (%s, %s, %s, %s, %s)
                            """, (title, description, response, json.dumps(tags), datetime.now()))
                conn.commit()

    def get_all_successful_responses(self):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                            SELECT id, task_title, my_response, tags, created_at
                            FROM successful_responses
                            ORDER BY created_at DESC
                            """)
                return cur.fetchall()

    def get_successful_response_by_id(self, response_id):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                            SELECT task_title, task_description, my_response, tags
                            FROM successful_responses
                            WHERE id = %s
                            """, (response_id,))
                return cur.fetchone()

    def delete_successful_response(self, response_id):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM successful_responses WHERE id = %s", (response_id,))
                conn.commit()

    def find_similar_responses(self, task_title, task_description, limit=3):
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
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM processed_orders WHERE order_id = %s", (order_id,))
                return cur.fetchone() is not None

    def mark_order_processed(self, order_id):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                            INSERT INTO processed_orders (order_id, processed_at)
                            VALUES (%s, %s) ON CONFLICT (order_id) DO NOTHING
                            """, (order_id, datetime.now()))
                conn.commit()

    # ========== Управление шаблонами ==========

    def get_template(self, name="default"):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT content FROM templates WHERE name = %s", (name,))
                result = cur.fetchone()
                return result[0] if result else None

    def set_template(self, name, content):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                            INSERT INTO templates (name, content)
                            VALUES (%s, %s) ON CONFLICT (name) DO
                            UPDATE SET content = EXCLUDED.content
                            """, (name, content))
                conn.commit()

    def get_all_templates(self):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT name, content FROM templates")
                return dict(cur.fetchall())

    # ========== Управление фильтрами ==========

    def get_filter(self, key):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT value FROM filters WHERE key = %s", (key,))
                result = cur.fetchone()
                return result[0] if result else None

    def set_filter(self, key, value):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                            INSERT INTO filters (key, value)
                            VALUES (%s, %s) ON CONFLICT (key) DO
                            UPDATE SET value = EXCLUDED.value
                            """, (key, value))
                conn.commit()

    def get_all_filters(self):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT key, value FROM filters")
                return dict(cur.fetchall())

    def get_filters_for_parser(self):
        """Получить фильтры в удобном для парсера формате"""
        filters = self.get_all_filters()
        return {
            "budget_min": int(filters.get("budget_min", 500)),
            "budget_max": int(filters.get("budget_max", 50000)),
            "keywords_include": [k.strip() for k in filters.get("keywords_include", "").split(",") if k.strip()],
            "keywords_exclude": [k.strip() for k in filters.get("keywords_exclude", "").split(",") if k.strip()],
        }


# Создаем глобальный экземпляр
db = Database()
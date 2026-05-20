import json
import re
import aiohttp
import asyncio
from database import db

class ResponseGenerator:
    def __init__(self):
        self.ollama_url = "http://localhost:11434"
        self.model = "saiga:7b"  # русскоязычная модель
        self.use_local_ai = True  # используем локальную нейросеть
        
    async def generate_response(self, project):
        """Генерирует отклик на основе успешных кейсов через локальную нейросеть"""
        # Получаем похожие успешные отклики
        similar_responses = db.find_similar_responses(
            project['title'], 
            project['description']
        )
        
        if not similar_responses:
            # Нет успешных примеров - используем шаблон
            return self.generate_from_template(project)
        
        # Есть успешные примеры - генерируем через локальную нейросеть
        return await self.generate_with_llama(project, similar_responses)
    
    async def generate_with_llama(self, project, similar_responses):
        """Генерирует отклик используя локальную Ollama + Saiga на основе успешных примеров"""
        # Формируем примеры успешных откликов
        examples_text = ""
        for i, (resp_id, title, response, tags) in enumerate(similar_responses[:3], 1):
            examples_text += f"\n--- Пример {i} ---\n"
            examples_text += f"Задача: {title}\n"
            examples_text += f"Мой отклик: {response}\n"
        
        # Промпт для нейросети
        prompt = f"""Ты - профессиональный фрилансер на бирже Kwork. Напиши отклик на заказ.

ВОТ ЗАКАЗ:
Название: {project['title']}
Описание: {project['description']}
Бюджет: {project['price']} ₽

ВОТ МОИ УСПЕШНЫЕ ОТКЛИКИ (по которым у меня были заказы):
{examples_text}

ТРЕБОВАНИЯ К ОТКЛИКУ:
1. Длина: 150-350 символов
2. Начинай с "Здравствуйте!" или "Добрый день!"
3. Покажи, что понял задачу (перефразируй своими словами)
4. Расскажи, как можешь помочь (опиши подход)
5. Упомяни свой опыт (общие слова, без конкретных брендов)
6. Закончи вопросом или призывом написать в личку
7. Используй стиль и структуру из моих успешных примеров
8. НЕ копируй примеры 1 в 1, адаптируй под текущую задачу

Напиши только текст отклика, без лишних комментариев."""

        try:
            # Запрос к локальной Ollama
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "max_tokens": 400
                        }
                    }
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        ai_response = result.get('response', '').strip()
                        if ai_response:
                            return self.clean_response(ai_response)
                    
                    # Если ошибка - используем fallback
                    print(f"Ошибка Ollama: статус {response.status}")
                    return self.generate_from_examples(project, similar_responses)
                    
        except aiohttp.ClientError as e:
            print(f"Не удалось подключиться к Ollama: {e}")
            print("Убедитесь, что Ollama запущен (ollama serve)")
            return self.generate_from_examples(project, similar_responses)
        except Exception as e:
            print(f"Ошибка генерации: {e}")
            return self.generate_from_examples(project, similar_responses)
    
    def generate_from_examples(self, project, similar_responses):
        """Простая генерация на основе успешных примеров (без AI - fallback)"""
        best_match = similar_responses[0]
        example_response = best_match[2]
        
        keywords = self.extract_keywords(project['title'] + " " + project['description'])
        keywords_str = ", ".join(keywords[:3])
        
        response = example_response.replace("{keywords}", keywords_str)
        
        if len(project['description']) > 30:
            context = project['description'][:50].strip()
            if context not in response:
                response = f"Понимаю задачу: {context}...\n\n{response}"
        
        if len(response) > 400:
            response = response[:397] + "..."
        
        return response
    
    def generate_from_template(self, project):
        """Шаблонная генерация (когда нет успешных примеров)"""
        template = db.get_template("default")
        if not template:
            template = "Здравствуйте! Я занимаюсь {keywords}. Сделаю качественно и в срок. Давайте обсудим детали."
        
        keywords = self.extract_keywords(project['title'] + " " + project['description'])
        keywords_str = ", ".join(keywords[:3])
        response = template.replace("{keywords}", keywords_str)
        
        return response
    
    def extract_keywords(self, text):
        """Извлекает ключевые слова из текста задачи"""
        keywords = []
        
        design_keywords = [
            'дизайн', 'оформление', 'логотип', 'фигма', 'фотошоп', 
            'иллюстратор', 'веб-дизайн', 'интерфейс', 'ui', 'ux',
            'баннер', 'презентация', 'визитка', 'полиграфия'
        ]
        
        text_lower = text.lower()
        
        for kw in design_keywords:
            if kw in text_lower:
                keywords.append(kw)
        
        if not keywords:
            keywords = ['дизайн']
        
        return keywords[:3]
    
    def clean_response(self, response):
        """Очищает и форматирует ответ"""
        response = response.strip('"\'')
        response = re.sub(r'\n{3,}', '\n\n', response)
        return response

response_gen = ResponseGenerator()

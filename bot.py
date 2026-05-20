import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from database import db
from response_generator import response_gen

class AddResponseStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_response = State()
    waiting_for_tags = State()

class KworkBot:
    def __init__(self, token, chat_id):
        self.bot = Bot(token=token)
        self.dp = Dispatcher(storage=MemoryStorage())
        self.chat_id = chat_id
        self.setup_handlers()
    
    def setup_handlers(self):
        # Основные команды
        self.dp.message.register(self.cmd_start, Command("start"))
        self.dp.message.register(self.cmd_help, Command("help"))
        
        # Работа с откликами
        self.dp.message.register(self.cmd_add_success, Command("add_success"))
        self.dp.message.register(self.cmd_list_success, Command("list_success"))
        self.dp.message.register(self.cmd_delete_success, Command("delete_success"))
        
        # Работа с фильтрами
        self.dp.message.register(self.cmd_filters, Command("filters"))
        self.dp.message.register(self.cmd_set_filter, Command("set_filter"))
        self.dp.message.register(self.cmd_set_category, Command("set_category"))
        
        # Состояния для добавления отклика
        self.dp.message.register(self.add_title, AddResponseStates.waiting_for_title)
        self.dp.message.register(self.add_description, AddResponseStates.waiting_for_description)
        self.dp.message.register(self.add_response_text, AddResponseStates.waiting_for_response)
        self.dp.message.register(self.add_tags, AddResponseStates.waiting_for_tags)
    
    async def cmd_start(self, message: Message):
        await message.answer(
            "🤖 БОТ ДЛЯ ПОИСКА ЗАКАЗОВ НА KWORK\n\n"
            "Я ищу новые заказы по вашим фильтрам и генерирую отклики.\n\n"
            "📌 КОМАНДЫ:\n"
            "/add_success - добавить успешный отклик\n"
            "/list_success - показать сохранённые отклики\n"
            "/delete_success - удалить отклик\n"
            "/filters - показать текущие фильтры\n"
            "/set_filter - изменить фильтр\n"
            "/set_category - сменить категорию\n"
            "/help - помощь"
        )
    
    async def cmd_help(self, message: Message):
        await message.answer(
            "📖 КАК ПОЛЬЗОВАТЬСЯ БОТОМ:\n\n"
            "1️⃣ Настройте категорию:\n"
            "   /set_category design\n\n"
            "2️⃣ Настройте фильтры:\n"
            "   /set_filter budget_min 1000\n"
            "   /set_filter budget_max 50000\n"
            "   /set_filter keywords_include дизайн,оформление\n"
            "   /set_filter keywords_exclude программирование\n\n"
            "3️⃣ Добавьте успешные отклики:\n"
            "   /add_success\n\n"
            "4️⃣ Бот сам ищет заказы раз в 3 минуты\n\n"
            "5️⃣ При получении заказа - копируете отклик\n"
            "   и отправляете на Kwork\n\n"
            "📂 Доступные категории:\n"
            "• design - дизайн\n"
            "• web_programming - программирование\n"
            "• copywriting - копирайтинг\n"
            "• seo - SEO и трафик\n"
            "• social - соцсети и маркетинг"
        )
    
    # ========== РАБОТА С ФИЛЬТРАМИ ==========
    
    async def cmd_filters(self, message: Message):
        """Показать текущие фильтры"""
        filters = db.get_all_filters()
        category = db.get_filter('category') or 'не задана'
        
        text = "🔧 ТЕКУЩИЕ НАСТРОЙКИ:\n\n"
        text += f"📂 Категория: {category}\n\n"
        text += f"💰 Мин. бюджет: {filters.get('budget_min', '500')} ₽\n"
        text += f"💰 Макс. бюджет: {filters.get('budget_max', '100000')} ₽\n\n"
        text += f"✅ КЛЮЧЕВЫЕ СЛОВА (должно содержать хотя бы одно):\n"
        keywords_include = filters.get('keywords_include', 'не заданы')
        text += f"   {keywords_include}\n\n"
        text += f"❌ ИСКЛЮЧАЕМЫЕ СЛОВА (если есть - заказ отсеется):\n"
        keywords_exclude = filters.get('keywords_exclude', 'не заданы')
        text += f"   {keywords_exclude}\n\n"
        text += "📝 КАК ИЗМЕНИТЬ:\n"
        text += "/set_category design\n"
        text += "/set_filter budget_min 1000\n"
        text += "/set_filter budget_max 50000\n"
        text += "/set_filter keywords_include дизайн,оформление\n"
        text += "/set_filter keywords_exclude программирование"
        
        await message.answer(text)
    
    async def cmd_set_filter(self, message: Message):
        """Установить фильтр: /set_filter budget_min 1000"""
        parts = message.text.split(maxsplit=2)
        
        if len(parts) < 3:
            await message.answer(
                "❌ НЕПРАВИЛЬНЫЙ ФОРМАТ\n\n"
                "Использование: /set_filter <ключ> <значение>\n\n"
                "Доступные ключи:\n"
                "• budget_min - минимальный бюджет\n"
                "• budget_max - максимальный бюджет\n"
                "• keywords_include - ключевые слова (через запятую)\n"
                "• keywords_exclude - исключаемые слова (через запятую)\n\n"
                "ПРИМЕРЫ:\n"
                "/set_filter budget_min 1000\n"
                "/set_filter keywords_include дизайн,оформление,логотип"
            )
            return
        
        key = parts[1]
        value = parts[2]
        
        # Валидация
        if key in ["budget_min", "budget_max"]:
            try:
                int(value)
            except ValueError:
                await message.answer("❌ Ошибка: бюджет должен быть числом!\nПример: /set_filter budget_min 1000")
                return
        
        # Сохраняем фильтр
        db.set_filter(key, value)
        await message.answer(f"✅ Фильтр '{key}' установлен в: {value}")
        
        # Показываем обновленные фильтры
        await self.cmd_filters(message)
    
    async def cmd_set_category(self, message: Message):
        """Установить категорию: /set_category design"""
        parts = message.text.split()
        
        if len(parts) < 2:
            await message.answer(
                "❌ НЕПРАВИЛЬНЫЙ ФОРМАТ\n\n"
                "Использование: /set_category <категория>\n\n"
                "Доступные категории:\n"
                "• design - дизайн\n"
                "• web_programming - программирование\n"
                "• copywriting - копирайтинг\n"
                "• seo - SEO и трафик\n"
                "• social - соцсети и маркетинг\n"
                "• audio - аудио и видео\n\n"
                "ПРИМЕР: /set_category design"
            )
            return
        
        category = parts[1]
        
        # Список доступных категорий
        valid_categories = ['design', 'web_programming', 'copywriting', 'seo', 'social', 'audio']
        
        if category not in valid_categories:
            await message.answer(f"❌ Категория '{category}' не найдена.\n\nДоступные категории: {', '.join(valid_categories)}")
            return
        
        db.set_filter('category', category)
        await message.answer(f"✅ Категория изменена на: {category}")
        
        # Показываем обновленные фильтры
        await self.cmd_filters(message)
    
    # ========== РАБОТА С УСПЕШНЫМИ ОТКЛИКАМИ ==========
    
    async def cmd_add_success(self, message: Message, state: FSMContext):
        await message.answer(
            "📝 ДОБАВЛЕНИЕ УСПЕШНОГО ОТКЛИКА\n\n"
            "Отправьте НАЗВАНИЕ задачи (с Kwork):"
        )
        await state.set_state(AddResponseStates.waiting_for_title)
    
    async def add_title(self, message: Message, state: FSMContext):
        await state.update_data(title=message.text)
        await message.answer("Отправьте ОПИСАНИЕ задачи (или /skip чтобы пропустить):")
        await state.set_state(AddResponseStates.waiting_for_description)
    
    async def add_description(self, message: Message, state: FSMContext):
        if message.text == "/skip":
            await state.update_data(description="")
        else:
            await state.update_data(description=message.text)
        
        await message.answer("Отправьте ТЕКСТ ВАШЕГО ОТКЛИКА, который привел к заказу:")
        await state.set_state(AddResponseStates.waiting_for_response)
    
    async def add_response_text(self, message: Message, state: FSMContext):
        await state.update_data(response=message.text)
        await message.answer("Отправьте ТЕГИ через запятую (например: дизайн, логотип, фигма) или /skip:")
        await state.set_state(AddResponseStates.waiting_for_tags)
    
    async def add_tags(self, message: Message, state: FSMContext):
        data = await state.get_data()
        
        if message.text != "/skip":
            tags = [tag.strip() for tag in message.text.split(",")]
        else:
            tags = []
        
        db.add_successful_response(
            title=data['title'],
            description=data.get('description', ''),
            response=data['response'],
            tags=tags
        )
        
        await message.answer(
            "✅ УСПЕШНЫЙ ОТКЛИК СОХРАНЕН!\n\n"
            "Теперь бот будет использовать его для генерации похожих откликов."
        )
        await state.clear()
    
    async def cmd_list_success(self, message: Message):
        responses = db.get_all_successful_responses()
        
        if not responses:
            await message.answer(
                "📭 У вас пока нет сохраненных откликов.\n\n"
                "Добавьте первый через /add_success"
            )
            return
        
        text = "📚 ВАШИ УСПЕШНЫЕ ОТКЛИКИ:\n\n"
        for resp_id, title, response, tags_json, created_at in responses[:10]:
            text += f"🆔 ID: {resp_id}\n"
            text += f"📌 Задача: {title[:50]}\n"
            text += f"💬 Отклик: {response[:80]}...\n"
            text += f"📅 Дата: {created_at[:10]}\n"
            text += "━━━━━━━━━━━━━━━━━━━━\n"
        
        text += "\n🗑️ Удалить: /delete_success <id>\n"
        text += "Пример: /delete_success 5"
        
        await message.answer(text)
    
    async def cmd_delete_success(self, message: Message):
        parts = message.text.split()
        if len(parts) < 2:
            await message.answer(
                "❌ Укажите ID отклика для удаления.\n"
                "Пример: /delete_success 5"
            )
            return
        
        try:
            resp_id = int(parts[1])
            db.delete_successful_response(resp_id)
            await message.answer(f"✅ Отклик с ID {resp_id} удален.")
        except ValueError:
            await message.answer("❌ ID должен быть числом.")
    
    # ========== ОТПРАВКА ЗАКАЗОВ ==========
    
    async def send_new_order(self, project, response_text):
        """Отправляет уведомление о новом заказе"""
        price_text = f"{project['price']} руб" if project['price'] > 0 else "Не указана"
        
        message = (
            f"🆕 НОВЫЙ ЗАКАЗ!\n\n"
            f"📌 Название: {project['title']}\n"
            f"💰 Бюджет: {price_text}\n"
            f"🔗 Ссылка: {project['url']}\n\n"
            f"💬 СГЕНЕРИРОВАННЫЙ ОТКЛИК (скопируйте):\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{response_text}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"✅ Скопируйте текст, перейдите по ссылке и отправьте!"
        )
        
        await self.bot.send_message(self.chat_id, message)
    
    async def start(self):
        await self.dp.start_polling(self.bot)

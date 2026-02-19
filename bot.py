# bot.py
import asyncio
import logging
import os
import re
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import asyncpg

from keyboards import main_menu, sections_menu, topics_keyboard, topic_navigation, admin_panel_menu
from states import PhysicsStates, AdminStates
import db_content

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════
# 👑 ТВОЙ TELEGRAM ID (ЗАМЕНИ НА СВОЙ)
# ═══════════════════════════════════════════════
ADMIN_ID = 8561318974  # ← СЮДА ТВОЙ ID

# Функция проверки админа
def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

# Функция для сброса вебхука
async def on_startup():
    logger.info("🔄 Сброс вебхука...")
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("✅ Вебхук удалён")

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Подключение к БД для админ-функций
async def get_connection():
    return await asyncpg.connect(DATABASE_URL)

# ═══════════════════════════════════════════════
# 👤 ОБЫЧНЫЕ ПОЛЬЗОВАТЕЛИ
# ═══════════════════════════════════════════════

# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user = message.from_user
    await db_content.add_user(user.id, user.username, user.first_name)
    
    admin_status = is_admin(user.id)
    
    welcome_text = (
        "🔬 *Добро пожаловать в бот-учебник по физике!*\n\n"
        "Здесь ты найдёшь:\n"
        "• Теорию по разделам физики\n"
        "• Формулы с пояснениями\n"
        "• Примеры решений\n"
        "• Тесты для самопроверки\n\n"
        "Выбери раздел в меню или напиши название темы."
    )
    
    if admin_status:
        welcome_text += "\n\n👑 *Режим администратора активен*"
    
    await message.answer(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=main_menu(is_admin=admin_status)
    )

# Обработчик кнопки "Разделы физики"
@dp.message(F.text == "📚 Разделы физики")
async def show_sections(message: types.Message, state: FSMContext):
    logger.info("📚 Нажата кнопка 'Разделы физики'")
    sections = await db_content.get_sections()
    
    if not sections:
        await message.answer("❌ Разделы временно недоступны")
        return
    
    await state.set_state(PhysicsStates.choosing_section)
    await message.answer(
        "Выбери раздел физики:",
        reply_markup=sections_menu(sections)
    )

# Обработчик возврата к разделам
@dp.message(F.text == "🔙 К разделам")
async def back_to_sections(message: types.Message, state: FSMContext):
    logger.info("🔙 Нажата кнопка 'К разделам'")
    await state.clear()
    
    sections = await db_content.get_sections()
    
    if sections:
        await message.answer(
            "📚 Выбери раздел физики:",
            reply_markup=sections_menu(sections)
        )
    else:
        await message.answer("❌ Разделы временно недоступны", 
                            reply_markup=main_menu(is_admin=is_admin(message.from_user.id)))

# Обработчик возврата в главное меню
@dp.message(F.text == "🔙 Главное меню")
async def back_to_main(message: types.Message, state: FSMContext):
    logger.info("🔙 Нажата кнопка 'Главное меню'")
    await state.clear()
    await message.answer(
        "Главное меню:",
        reply_markup=main_menu(is_admin=is_admin(message.from_user.id))
    )

# Помощь
@dp.message(F.text == "❓ Помощь")
async def help(message: types.Message):
    help_text = (
        "🔍 *Как пользоваться ботом*\n\n"
        "• Нажми '📚 Разделы физики' и выбери тему\n"
        "• Внутри темы можно посмотреть теорию, формулы, примеры\n"
        "• Скоро появятся тесты для самопроверки\n\n"
        "Или просто напиши название темы (например, 'кинематика')"
    )
    await message.answer(help_text, parse_mode="Markdown")

# Обработчик выбора раздела
@dp.message(PhysicsStates.choosing_section)
async def section_chosen(message: types.Message, state: FSMContext):
    text = message.text
    clean_name = text[2:].strip() if len(text) > 2 and text[0].isdigit() and text[1] in '️️⃣' else text
    
    sections = await db_content.get_sections()
    
    selected_section = None
    for section in sections:
        if section['name'] in clean_name:
            selected_section = section
            break
    
    if selected_section:
        await state.update_data(section_id=selected_section['id'], section_key=selected_section['key'])
        
        topics = await db_content.get_topics(selected_section['id'])
        
        if topics:
            await state.set_state(PhysicsStates.choosing_topic)
            await message.answer(
                f"📌 *{selected_section['name']}*\n\nВыбери тему:",
                parse_mode="Markdown",
                reply_markup=topics_keyboard(topics)
            )
        else:
            await message.answer("В этом разделе пока нет тем")
    else:
        await message.answer("Раздел не найден. Попробуй ещё раз.")

# Обработчик выбора темы
@dp.message(PhysicsStates.choosing_topic)
async def topic_chosen(message: types.Message, state: FSMContext):
    if message.text in ["🔙 К разделам", "🔙 Главное меню"]:
        return
    
    data = await state.get_data()
    section_id = data.get('section_id')
    
    if not section_id:
        await message.answer("Ошибка. Начни сначала.")
        await state.clear()
        return
    
    topics = await db_content.get_topics(section_id)
    
    if not topics:
        await message.answer("❌ В этом разделе пока нет тем")
        return
    
    selected_topic = None
    for topic in topics:
        if topic['name'].strip().lower() == message.text.strip().lower():
            selected_topic = topic
            break
    
    if selected_topic:
        await state.update_data(topic_id=selected_topic['id'])
        await message.answer(
            f"*{selected_topic['name']}*\n\n📖 *Теория:*\n{selected_topic['theory']}",
            parse_mode="Markdown",
            reply_markup=topic_navigation()
        )
    else:
        topics_list = "\n".join([f"• {t['name']}" for t in topics])
        await message.answer(
            f"❌ Тема не найдена.\n\nДоступные темы:\n{topics_list}\n\nПожалуйста, выбери тему из списка:",
            reply_markup=topics_keyboard(topics)
        )

# Обработчик кнопки "Формулы"
@dp.callback_query(F.data == "show_formulas")
async def show_formulas(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    topic_id = data.get('topic_id')
    
    if not topic_id:
        await callback.message.answer("Ошибка. Начни сначала.")
        return
    
    formulas = await db_content.get_formulas(topic_id)
    
    if not formulas:
        await callback.message.answer("Формул пока нет.")
        return
    
    text = "📐 *Формулы:*\n\n"
    for i, f in enumerate(formulas, 1):
        text += f"{i}. *{f['formula']}*\n"
        if f['description']:
            text += f"   _{f['description']}_\n\n"
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=topic_navigation())
    await callback.answer()

# Обработчик кнопки "Теория"
@dp.callback_query(F.data == "show_theory")
async def show_theory(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    topic_id = data.get('topic_id')
    
    if not topic_id:
        await callback.message.answer("Ошибка. Начни сначала.")
        return
    
    topic = await db_content.get_topic_by_id(topic_id)
    
    if not topic:
        await callback.message.answer("Теория не найдена.")
        return
    
    await callback.message.edit_text(
        f"*{topic['name']}*\n\n📖 *Теория:*\n{topic['theory']}",
        parse_mode="Markdown",
        reply_markup=topic_navigation()
    )
    await callback.answer()

# Обработчик кнопки "Примеры"
@dp.callback_query(F.data == "show_examples")
async def show_examples(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    topic_id = data.get('topic_id')
    
    if not topic_id:
        await callback.message.answer("Ошибка. Начни сначала.")
        return
    
    examples = await db_content.get_examples(topic_id)
    
    if not examples:
        await callback.message.answer("Примеров пока нет.")
        return
    
    text = "📝 *Примеры:*\n\n"
    for i, ex in enumerate(examples, 1):
        text += f"*Задача {i}:* {ex['question']}\n"
        text += f"*Решение:* {ex['answer']}\n\n"
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=topic_navigation())
    await callback.answer()

# Обработчик возврата к темам
@dp.callback_query(F.data == "back_to_topics")
async def back_to_topics(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    section_id = data.get('section_id')
    
    if section_id:
        topics = await db_content.get_topics(section_id)
        if topics:
            await state.set_state(PhysicsStates.choosing_topic)
            
            section = await db_content.get_section_by_id(section_id)
            section_name = section['name'] if section else "Раздел"
            
            await callback.message.answer(
                f"📌 *{section_name}*\n\nВыбери тему:",
                parse_mode="Markdown",
                reply_markup=topics_keyboard(topics)
            )
            await callback.message.delete()
        else:
            await callback.message.answer("❌ В этом разделе пока нет тем")
    else:
        await callback.message.answer("❌ Ошибка. Начни сначала.", 
                                     reply_markup=main_menu(is_admin=is_admin(callback.from_user.id)))
        await state.clear()
    
    await callback.answer()

# Обработчик поиска
@dp.message(F.text == "🔍 Поиск по формуле")
async def search_formula(message: types.Message):
    await message.answer("🔍 Функция поиска по формулам появится скоро!")

# ═══════════════════════════════════════════════
# 👑 АДМИН-ПАНЕЛЬ
# ═══════════════════════════════════════════════

@dp.message(F.text == "🔧 Админ панель")
async def admin_panel(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет доступа к админ-панели.")
        return
    
    await state.set_state(AdminStates.choosing_action)
    await message.answer(
        "👑 *Админ-панель*\n\nВыбери действие:",
        parse_mode="Markdown",
        reply_markup=admin_panel_menu()
    )

@dp.message(F.text == "◀️ Назад в главное меню")
async def back_to_main_from_admin(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Главное меню:",
        reply_markup=main_menu(is_admin=is_admin(message.from_user.id))
    )

# Словарь для транслитерации
TRANSLIT_DICT = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
    'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
    'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'Yo',
    'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M',
    'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
    'Ф': 'F', 'Х': 'H', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Sch',
    'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya'
}

def transliterate(text: str) -> str:
    """Транслитерация с русского на латиницу"""
    result = ''
    for char in text:
        result += TRANSLIT_DICT.get(char, char)
    return result

# Добавление раздела
@dp.message(AdminStates.choosing_action, F.text == "📚 Добавить раздел")
async def add_section_start(message: types.Message, state: FSMContext):
    await state.set_state(AdminStates.adding_section)
    await message.answer(
        "📚 *Добавление раздела*\n\n"
        "Введи название раздела (например: 'Квантовая физика'):",
        parse_mode="Markdown"
    )

@dp.message(AdminStates.adding_section)
async def add_section_process(message: types.Message, state: FSMContext):
    section_name = message.text.strip()
    
    # Транслитерация
    latin_name = transliterate(section_name)
    # Заменяем пробелы на _, убираем всё кроме букв и цифр
    section_key = re.sub(r'[^a-zA-Z0-9_]', '', latin_name.replace(' ', '_')).lower()
    
    conn = await get_connection()
    try:
        await conn.execute(
            "INSERT INTO sections (key, name) VALUES ($1, $2)",
            section_key, section_name
        )
        await message.answer(f"✅ Раздел '{section_name}' добавлен!\n🔑 Ключ: {section_key}")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
    finally:
        await conn.close()
    
    await state.set_state(AdminStates.choosing_action)
    await message.answer("Выбери действие:", reply_markup=admin_panel_menu())

# Добавление темы
@dp.message(AdminStates.choosing_action, F.text == "📖 Добавить тему")
async def add_topic_start(message: types.Message, state: FSMContext):
    sections = await db_content.get_sections()
    
    if not sections:
        await message.answer("❌ Сначала добавь раздел!")
        return
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = []
    for section in sections:
        kb.append([InlineKeyboardButton(
            text=section['name'],
            callback_data=f"admin_topic_section_{section['id']}"
        )])
    
    await message.answer(
        "Выбери раздел для новой темы:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )
    await state.set_state(AdminStates.adding_topic_choose_section)

@dp.callback_query(AdminStates.adding_topic_choose_section, F.data.startswith("admin_topic_section_"))
async def add_topic_choose_section(callback: types.CallbackQuery, state: FSMContext):
    section_id = int(callback.data.split("_")[3])
    await state.update_data(section_id=section_id)
    
    await callback.message.edit_text("📖 Введи название темы:")
    await state.set_state(AdminStates.adding_topic_name)
    await callback.answer()

@dp.message(AdminStates.adding_topic_name)
async def add_topic_name(message: types.Message, state: FSMContext):
    topic_name = message.text.strip()
    await state.update_data(topic_name=topic_name)
    
    await message.answer("📖 Введи теорию для этой темы (можно несколько строк):")
    await state.set_state(AdminStates.adding_topic_theory)

@dp.message(AdminStates.adding_topic_theory)
async def add_topic_theory(message: types.Message, state: FSMContext):
    theory = message.text.strip()
    data = await state.get_data()
    
    # Генерируем ключ темы
    latin_name = transliterate(data['topic_name'])
    topic_key = re.sub(r'[^a-zA-Z0-9_]', '', latin_name.replace(' ', '_')).lower()
    
    conn = await get_connection()
    try:
        await conn.execute(
            "INSERT INTO topics (section_id, key, name, theory) VALUES ($1, $2, $3, $4)",
            data['section_id'], topic_key, data['topic_name'], theory
        )
        await message.answer(f"✅ Тема '{data['topic_name']}' добавлена!")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
    finally:
        await conn.close()
    
    await state.set_state(AdminStates.choosing_action)
    await message.answer("Выбери действие:", reply_markup=admin_panel_menu())

# Добавление формулы
@dp.message(AdminStates.choosing_action, F.text == "📐 Добавить формулу")
async def add_formula_start(message: types.Message, state: FSMContext):
    sections = await db_content.get_sections()
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = []
    for section in sections:
        kb.append([InlineKeyboardButton(
            text=section['name'],
            callback_data=f"admin_formula_section_{section['id']}"
        )])
    
    await message.answer(
        "Выбери раздел:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )
    await state.set_state(AdminStates.adding_formula_choose_topic)

@dp.callback_query(F.data.startswith("admin_formula_section_"))
async def add_formula_choose_section(callback: types.CallbackQuery, state: FSMContext):
    section_id = int(callback.data.split("_")[3])
    
    topics = await db_content.get_topics(section_id)
    
    if not topics:
        await callback.message.edit_text("❌ В этом разделе нет тем. Сначала добавь тему.")
        return
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = []
    for topic in topics:
        kb.append([InlineKeyboardButton(
            text=topic['name'],
            callback_data=f"admin_formula_topic_{topic['id']}"
        )])
    
    await callback.message.edit_text(
        "Выбери тему для формулы:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )
    await state.set_state(AdminStates.adding_formula_choose_topic)
    await callback.answer()

@dp.callback_query(F.data.startswith("admin_formula_topic_"))
async def add_formula_choose_topic(callback: types.CallbackQuery, state: FSMContext):
    topic_id = int(callback.data.split("_")[3])
    await state.update_data(topic_id=topic_id)
    
    await callback.message.edit_text("📐 Введи название формулы:")
    await state.set_state(AdminStates.adding_formula_name)
    await callback.answer()

@dp.message(AdminStates.adding_formula_name)
async def add_formula_name(message: types.Message, state: FSMContext):
    formula_name = message.text.strip()
    await state.update_data(formula_name=formula_name)
    
    await message.answer("📐 Введи саму формулу (например: 'F = ma'):")
    await state.set_state(AdminStates.adding_formula_text)

@dp.message(AdminStates.adding_formula_text)
async def add_formula_text(message: types.Message, state: FSMContext):
    formula_text = message.text.strip()
    await state.update_data(formula_text=formula_text)
    
    await message.answer("📐 Введи описание (или '-' если не нужно):")
    await state.set_state(AdminStates.adding_formula_desc)

@dp.message(AdminStates.adding_formula_desc)
async def add_formula_desc(message: types.Message, state: FSMContext):
    description = message.text.strip()
    if description == '-':
        description = ''
    
    data = await state.get_data()
    
    conn = await get_connection()
    try:
        await conn.execute(
            "INSERT INTO formulas (topic_id, name, formula, description) VALUES ($1, $2, $3, $4)",
            data['topic_id'], data['formula_name'], data['formula_text'], description
        )
        await message.answer(f"✅ Формула '{data['formula_name']}' добавлена!")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
    finally:
        await conn.close()
    
    await state.set_state(AdminStates.choosing_action)
    await message.answer("Выбери действие:", reply_markup=admin_panel_menu())

# Добавление примера
@dp.message(AdminStates.choosing_action, F.text == "📝 Добавить пример")
async def add_example_start(message: types.Message, state: FSMContext):
    sections = await db_content.get_sections()
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = []
    for section in sections:
        kb.append([InlineKeyboardButton(
            text=section['name'],
            callback_data=f"admin_example_section_{section['id']}"
        )])
    
    await message.answer(
        "Выбери раздел:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )
    await state.set_state(AdminStates.adding_example_choose_topic)

@dp.callback_query(F.data.startswith("admin_example_section_"))
async def add_example_choose_section(callback: types.CallbackQuery, state: FSMContext):
    section_id = int(callback.data.split("_")[3])
    
    topics = await db_content.get_topics(section_id)
    
    if not topics:
        await callback.message.edit_text("❌ В этом разделе нет тем. Сначала добавь тему.")
        return
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = []
    for topic in topics:
        kb.append([InlineKeyboardButton(
            text=topic['name'],
            callback_data=f"admin_example_topic_{topic['id']}"
        )])
    
    await callback.message.edit_text(
        "Выбери тему для примера:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )
    await state.set_state(AdminStates.adding_example_choose_topic)
    await callback.answer()

@dp.callback_query(F.data.startswith("admin_example_topic_"))
async def add_example_choose_topic(callback: types.CallbackQuery, state: FSMContext):
    topic_id = int(callback.data.split("_")[3])
    await state.update_data(topic_id=topic_id)
    
    await callback.message.edit_text("📝 Введи условие задачи:")
    await state.set_state(AdminStates.adding_example_question)
    await callback.answer()

@dp.message(AdminStates.adding_example_question)
async def add_example_question(message: types.Message, state: FSMContext):
    question = message.text.strip()
    await state.update_data(question=question)
    
    await message.answer("📝 Введи ответ/решение:")
    await state.set_state(AdminStates.adding_example_answer)

@dp.message(AdminStates.adding_example_answer)
async def add_example_answer(message: types.Message, state: FSMContext):
    answer = message.text.strip()
    data = await state.get_data()
    
    conn = await get_connection()
    try:
        await conn.execute(
            "INSERT INTO examples (topic_id, question, answer) VALUES ($1, $2, $3)",
            data['topic_id'], data['question'], answer
        )
        await message.answer(f"✅ Пример добавлен!")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
    finally:
        await conn.close()
    
    await state.set_state(AdminStates.choosing_action)
    await message.answer("Выбери действие:", reply_markup=admin_panel_menu())

# Список разделов для админа
@dp.message(AdminStates.choosing_action, F.text == "📋 Список разделов")
async def admin_list_sections(message: types.Message):
    conn = await get_connection()
    rows = await conn.fetch("""
        SELECT s.id, s.name, COUNT(t.id) as topics_count 
        FROM sections s 
        LEFT JOIN topics t ON s.id = t.section_id 
        GROUP BY s.id 
        ORDER BY s.id
    """)
    await conn.close()
    
    text = "📚 *Разделы:*\n\n"
    for row in rows:
        text += f"• {row['name']} — {row['topics_count']} тем\n"
    
    await message.answer(text, parse_mode="Markdown")

# ═══════════════════════════════════════════════
# ЗАПУСК БОТА
# ═══════════════════════════════════════════════

async def main():
    await on_startup()
    try:
        logger.info("🚀 Бот запускается...")
        await dp.start_polling(bot)
    finally:
        logger.info("👋 Бот останавливается...")
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())

# bot.py
import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

from keyboards import main_menu, sections_menu, topics_keyboard, topic_navigation
from states import PhysicsStates
import db_content  # импортируем наш модуль для работы с БД

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Функция для сброса вебхука
async def on_startup():
    logger.info("🔄 Сброс вебхука...")
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("✅ Вебхук удалён")

# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🔬 *Добро пожаловать в бот-учебник по физике!*\n\n"
        "Здесь ты найдёшь:\n"
        "• Теорию по разделам физики\n"
        "• Формулы с пояснениями\n"
        "• Примеры решений\n"
        "• Тесты для самопроверки\n\n"
        "Выбери раздел в меню или напиши название темы.",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

# Обработчик кнопки "Разделы физики"
@dp.message(F.text == "📚 Разделы физики")
async def show_sections(message: types.Message, state: FSMContext):
    logger.info("📚 Нажата кнопка 'Разделы физики'")
    # Получаем разделы из БД
    sections = await db_content.get_sections()
    
    if not sections:
        await message.answer("❌ Разделы временно недоступны")
        return
    
    await state.set_state(PhysicsStates.choosing_section)
    await message.answer(
        "Выбери раздел физики:",
        reply_markup=sections_menu(sections)
    )

# ВАЖНО: Обработчик возврата к разделам должен быть ПЕРЕД обработчиком выбора темы
@dp.message(F.text == "🔙 К разделам")
async def back_to_sections(message: types.Message, state: FSMContext):
    logger.info("🔙 Нажата кнопка 'К разделам'")
    # Очищаем состояние
    await state.clear()
    
    # Получаем все разделы из БД
    sections = await db_content.get_sections()
    
    if sections:
        await message.answer(
            "📚 Выбери раздел физики:",
            reply_markup=sections_menu(sections)
        )
    else:
        await message.answer("❌ Разделы временно недоступны", reply_markup=main_menu())

# Обработчик возврата в главное меню
@dp.message(F.text == "🔙 Главное меню")
async def back_to_main(message: types.Message, state: FSMContext):
    logger.info("🔙 Нажата кнопка 'Главное меню'")
    await state.clear()
    await message.answer("Главное меню:", reply_markup=main_menu())

# Помощь
@dp.message(F.text == "❓ Помощь")
async def help(message: types.Message):
    logger.info("❓ Нажата кнопка 'Помощь'")
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
    logger.info(f"📌 Выбор раздела: '{text}'")
    
    # Извлекаем название раздела (убираем эмодзи)
    clean_name = text[2:].strip() if len(text) > 2 and text[0].isdigit() and text[1] in '️️⃣' else text
    
    # Получаем все разделы
    sections = await db_content.get_sections()
    
    # Ищем выбранный раздел
    selected_section = None
    for section in sections:
        if section['name'] in clean_name:
            selected_section = section
            break
    
    if selected_section:
        logger.info(f"✅ Выбран раздел: {selected_section['name']} (ID: {selected_section['id']})")
        await state.update_data(section_id=selected_section['id'], section_key=selected_section['key'])
        
        # Получаем темы раздела
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
        logger.warning(f"❌ Раздел не найден: '{text}'")
        await message.answer("Раздел не найден. Попробуй ещё раз.")

# Обработчик выбора темы
@dp.message(PhysicsStates.choosing_topic)
async def topic_chosen(message: types.Message, state: FSMContext):
    # Логируем всё, что приходит
    logger.info(f"🔍 Вход в topic_chosen с текстом: '{message.text}'")
    
    # Проверяем, не нажата ли случайно кнопка возврата
    if message.text == "🔙 К разделам":
        logger.info("🔙 Кнопка 'К разделам' перехвачена в topic_chosen, но это не должно происходить")
        return
    
    if message.text == "🔙 Главное меню":
        logger.info("🔙 Кнопка 'Главное меню' перехвачена в topic_chosen, но это не должно происходить")
        return
    
    data = await state.get_data()
    section_id = data.get('section_id')
    
    logger.info(f"📊 section_id из состояния: {section_id}")
    
    if not section_id:
        logger.warning("❌ Нет section_id в состоянии")
        await message.answer("Ошибка. Начни сначала.")
        await state.clear()
        return
    
    # Получаем все темы раздела
    topics = await db_content.get_topics(section_id)
    logger.info(f"📚 Найдено тем в БД: {len(topics)}")
    
    if not topics:
        await message.answer("❌ В этом разделе пока нет тем")
        return
    
    # Ищем выбранную тему
    selected_topic = None
    for topic in topics:
        logger.info(f"Сравниваю '{topic['name'].strip().lower()}' с '{message.text.strip().lower()}'")
        if topic['name'].strip().lower() == message.text.strip().lower():
            selected_topic = topic
            break
    
    if selected_topic:
        logger.info(f"✅ Найдена тема: {selected_topic['name']} (ID: {selected_topic['id']})")
        await state.update_data(topic_id=selected_topic['id'])
        
        await message.answer(
            f"*{selected_topic['name']}*\n\n📖 *Теория:*\n{selected_topic['theory']}",
            parse_mode="Markdown",
            reply_markup=topic_navigation()
        )
    else:
        logger.warning(f"❌ Тема не найдена: '{message.text}'")
        # Показываем доступные темы
        topics_list = "\n".join([f"• {t['name']}" for t in topics])
        await message.answer(
            f"❌ Тема не найдена.\n\nДоступные темы:\n{topics_list}\n\nПожалуйста, выбери тему из списка:",
            reply_markup=topics_keyboard(topics)
        )

# Обработчик кнопки "Формулы"
@dp.callback_query(F.data == "show_formulas")
async def show_formulas(callback: types.CallbackQuery, state: FSMContext):
    logger.info("📐 Нажата кнопка 'Формулы'")
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
    logger.info("📖 Нажата кнопка 'Теория'")
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
    logger.info("📝 Нажата кнопка 'Примеры'")
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
    logger.info("🔙 Нажата инлайн-кнопка 'К темам'")
    data = await state.get_data()
    section_id = data.get('section_id')
    
    if section_id:
        # Получаем темы раздела
        topics = await db_content.get_topics(section_id)
        if topics:
            # Устанавливаем состояние выбора темы
            await state.set_state(PhysicsStates.choosing_topic)
            
            # Получаем название раздела
            section = await db_content.get_section_by_id(section_id)
            section_name = section['name'] if section else "Раздел"
            
            # Отправляем новое сообщение с темами
            await callback.message.answer(
                f"📌 *{section_name}*\n\nВыбери тему:",
                parse_mode="Markdown",
                reply_markup=topics_keyboard(topics)
            )
            # Удаляем старое сообщение с инлайн-кнопками
            await callback.message.delete()
        else:
            await callback.message.answer("❌ В этом разделе пока нет тем")
    else:
        await callback.message.answer("❌ Ошибка. Начни сначала.", reply_markup=main_menu())
        await state.clear()
    
    await callback.answer()

# Обработчик поиска по формуле (пока заглушка)
@dp.message(F.text == "🔍 Поиск по формуле")
async def search_formula(message: types.Message):
    logger.info("🔍 Нажата кнопка 'Поиск по формуле'")
    await message.answer("🔍 Функция поиска по формулам появится скоро!")

# Запуск бота
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

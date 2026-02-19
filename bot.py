# bot.py
import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

from keyboards import main_menu, sections_menu, topic_navigation
from states import PhysicsStates
from physics_data import physics_content

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

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
    await state.set_state(PhysicsStates.choosing_section)
    await message.answer(
        "Выбери раздел физики:",
        reply_markup=sections_menu()
    )

# Обработчик выбора раздела
@dp.message(PhysicsStates.choosing_section, F.text.in_(["1️⃣ Механика", "2️⃣ Молекулярная физика", "3️⃣ Электричество", "4️⃣ Оптика"]))
async def section_chosen(message: types.Message, state: FSMContext):
    section_map = {
        "1️⃣ Механика": "mechanics",
        "2️⃣ Молекулярная физика": "molecular",
        "3️⃣ Электричество": "electricity",
        "4️⃣ Оптика": "optics"
    }
    
    section_key = section_map.get(message.text)
    if section_key and section_key in physics_content:
        await state.update_data(section=section_key)
        await state.set_state(PhysicsStates.choosing_topic)
        
        # Показываем темы выбранного раздела
        section = physics_content[section_key]
        topics_text = f"📌 *{section['name']}*\n\nДоступные темы:\n"
        
        # Создаем клавиатуру с темами
        from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
        topics_keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=topic['name'])] for topic in section['topics'].values()] + 
                     [[KeyboardButton(text="🔙 К разделам")]],
            resize_keyboard=True
        )
        
        await message.answer("Выбери тему:", reply_markup=topics_keyboard)

# Обработчик выбора темы
@dp.message(PhysicsStates.choosing_topic)
async def topic_chosen(message: types.Message, state: FSMContext):
    data = await state.get_data()
    section_key = data.get('section')
    
    if not section_key or section_key not in physics_content:
        await message.answer("Ошибка. Начни сначала.")
        await state.clear()
        return
    
    section = physics_content[section_key]
    
    # Ищем выбранную тему
    selected_topic = None
    topic_key = None
    for key, topic in section['topics'].items():
        if topic['name'].lower() in message.text.lower() or message.text.lower() in topic['name'].lower():
            selected_topic = topic
            topic_key = key
            break
    
    if selected_topic:
        await state.update_data(topic=topic_key)
        
        # Отправляем информацию о теме
        text = f"*{selected_topic['name']}*\n\n"
        text += f"📖 *Теория:*\n{selected_topic['theory']}\n\n"
        
        await message.answer(text, parse_mode="Markdown", reply_markup=topic_navigation())
    else:
        await message.answer("Тема не найдена. Попробуй ещё раз.")

# Обработчик кнопки "Формулы"
@dp.callback_query(F.data == "show_formulas")
async def show_formulas(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    section_key = data.get('section')
    topic_key = data.get('topic')
    
    if not section_key or not topic_key:
        await callback.message.answer("Ошибка. Начни сначала.")
        return
    
    topic = physics_content[section_key]['topics'][topic_key]
    
    text = f"*{topic['name']}: формулы*\n\n"
    for i, formula in enumerate(topic['formulas'], 1):
        text += f"{i}. *{formula['formula']}*\n"
        text += f"   _{formula['description']}_\n\n"
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=topic_navigation())
    await callback.answer()

# Обработчик кнопки "Теория"
@dp.callback_query(F.data == "show_theory")
async def show_theory(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    section_key = data.get('section')
    topic_key = data.get('topic')
    
    if not section_key or not topic_key:
        await callback.message.answer("Ошибка. Начни сначала.")
        return
    
    topic = physics_content[section_key]['topics'][topic_key]
    
    text = f"*{topic['name']}: теория*\n\n{topic['theory']}"
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=topic_navigation())
    await callback.answer()

# Обработчик кнопки "Примеры"
@dp.callback_query(F.data == "show_examples")
async def show_examples(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    section_key = data.get('section')
    topic_key = data.get('topic')
    
    if not section_key or not topic_key:
        await callback.message.answer("Ошибка. Начни сначала.")
        return
    
    topic = physics_content[section_key]['topics'][topic_key]
    
    if not topic.get('examples'):
        await callback.message.answer("Примеров пока нет.")
        return
    
    text = f"*{topic['name']}: примеры*\n\n"
    for i, example in enumerate(topic['examples'], 1):
        text += f"*Задача {i}:* {example['question']}\n"
        text += f"*Решение:* {example['answer']}\n\n"
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=topic_navigation())
    await callback.answer()

# Обработчик возврата к темам
@dp.callback_query(F.data == "back_to_topics")
async def back_to_topics(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    section_key = data.get('section')
    
    if section_key and section_key in physics_content:
        section = physics_content[section_key]
        
        from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
        topics_keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=topic['name'])] for topic in section['topics'].values()] + 
                     [[KeyboardButton(text="🔙 К разделам")]],
            resize_keyboard=True
        )
        
        await callback.message.answer("Выбери тему:", reply_markup=topics_keyboard)
        await state.set_state(PhysicsStates.choosing_topic)
    else:
        await callback.message.answer("Ошибка. Начни сначала.")
        await state.clear()
    
    await callback.answer()

# Обработчик возврата к разделам
@dp.message(F.text == "🔙 К разделам")
async def back_to_sections(message: types.Message, state: FSMContext):
    await state.set_state(PhysicsStates.choosing_section)
    await message.answer("Выбери раздел физики:", reply_markup=sections_menu())

# Обработчик возврата в главное меню
@dp.message(F.text == "🔙 Главное меню")
async def back_to_main(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню:", reply_markup=main_menu())

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

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
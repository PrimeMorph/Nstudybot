# keyboards.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# Главное меню
def main_menu():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="📚 Разделы физики"))
    builder.add(KeyboardButton(text="🔍 Поиск по формуле"))
    builder.add(KeyboardButton(text="❓ Помощь"))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

# Меню разделов физики
def sections_menu():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="1️⃣ Механика"))
    builder.add(KeyboardButton(text="2️⃣ Молекулярная физика"))
    builder.add(KeyboardButton(text="3️⃣ Электричество"))
    builder.add(KeyboardButton(text="4️⃣ Оптика"))
    builder.add(KeyboardButton(text="🔙 Главное меню"))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

# Кнопки для навигации внутри темы
def topic_navigation():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="📐 Формулы", callback_data="show_formulas"))
    builder.add(InlineKeyboardButton(text="📋 Теория", callback_data="show_theory"))
    builder.add(InlineKeyboardButton(text="📝 Примеры", callback_data="show_examples"))
    builder.add(InlineKeyboardButton(text="🧪 Тест", callback_data="start_test"))
    builder.add(InlineKeyboardButton(text="🔙 К темам", callback_data="back_to_topics"))
    builder.adjust(2)
    return builder.as_markup()
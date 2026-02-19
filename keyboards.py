# keyboards.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# Главное меню (теперь с параметром is_admin)
def main_menu(is_admin: bool = False):
    builder = ReplyKeyboardBuilder()
    
    # Основные кнопки для всех
    builder.add(KeyboardButton(text="📚 Разделы физики"))
    builder.add(KeyboardButton(text="🔍 Поиск по формуле"))
    builder.add(KeyboardButton(text="❓ Помощь"))
    
    # Админские кнопки (только для админа)
    if is_admin:
        builder.add(KeyboardButton(text="🔧 Админ панель"))
    
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

# Меню разделов (динамическое)
def sections_menu(sections: list):
    builder = ReplyKeyboardBuilder()
    for section in sections:
        # Добавляем эмодзи в зависимости от названия
        emoji = "1️⃣" if "Механика" in section['name'] else "2️⃣" if "Молекулярная" in section['name'] else "3️⃣" if "Электричество" in section['name'] else "4️⃣"
        builder.add(KeyboardButton(text=f"{emoji} {section['name']}"))
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

# Клавиатура для списка тем
def topics_keyboard(topics: list):
    builder = ReplyKeyboardBuilder()
    for topic in topics:
        builder.add(KeyboardButton(text=topic['name']))
    builder.add(KeyboardButton(text="🔙 К разделам"))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

# Админ-панель меню
def admin_panel_menu():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="📚 Добавить раздел"))
    builder.add(KeyboardButton(text="📖 Добавить тему"))
    builder.add(KeyboardButton(text="📐 Добавить формулу"))
    builder.add(KeyboardButton(text="📝 Добавить пример"))
    builder.add(KeyboardButton(text="📋 Список разделов"))
    builder.add(KeyboardButton(text="◀️ Назад в главное меню"))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

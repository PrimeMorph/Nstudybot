# states.py
from aiogram.fsm.state import State, StatesGroup

class PhysicsStates(StatesGroup):
    """Состояния для навигации по физике"""
    choosing_section = State()      # выбор раздела
    choosing_topic = State()        # выбор темы внутри раздела
    viewing_formula = State()       # просмотр формулы
    viewing_example = State()       # просмотр примера
    taking_test = State()           # прохождение теста

class AdminStates(StatesGroup):
    """Состояния для админ-панели"""
    choosing_action = State()
    adding_section = State()
    adding_topic_choose_section = State()
    adding_topic_name = State()
    adding_topic_theory = State()
    adding_formula_choose_topic = State()
    adding_formula_name = State()
    adding_formula_text = State()
    adding_formula_desc = State()
    adding_example_choose_topic = State()
    adding_example_question = State()
    adding_example_answer = State()

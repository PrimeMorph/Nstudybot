# states.py
from aiogram.fsm.state import State, StatesGroup

class PhysicsStates(StatesGroup):
    """Состояния для навигации по физике"""
    choosing_section = State()      # выбор раздела (механика, электричество...)
    choosing_topic = State()        # выбор темы внутри раздела
    viewing_formula = State()       # просмотр конкретной формулы
    viewing_example = State()       # просмотр примера
    taking_test = State()           # прохождение теста
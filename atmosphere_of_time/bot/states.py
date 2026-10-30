"""FSM-состояния для пошаговых сценариев."""
from aiogram.fsm.state import State, StatesGroup


class OrderStates(StatesGroup):
    """Оформление заказа."""
    name = State()
    phone = State()
    address = State()
    comment = State()
    payment = State()


class SearchStates(StatesGroup):
    """Поиск по каталогу."""
    query = State()


class AdminProductStates(StatesGroup):
    """Добавление товара (админ)."""
    name = State()
    brand = State()
    category = State()
    description = State()
    top_notes = State()
    heart_notes = State()
    base_notes = State()
    volumes = State()       # формат: 30:2500,50:3500,100:5500
    stock = State()
    photo = State()


class AdminPriceStates(StatesGroup):
    """Изменение цен (админ)."""
    volumes = State()


class ProfileStates(StatesGroup):
    """Редактирование профиля."""
    edit_name = State()
    edit_phone = State()
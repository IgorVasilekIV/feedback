from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_ID
# Импортируем функции БД
from database import add_ban, remove_ban

admin_router = Router()

# Состояния для FSM (режим ответа)
class AdminAnswer(StatesGroup):
    waiting_for_answer = State()
    target_user_id = State()

# --- КОМАНДЫ РУЧНОГО БАНА/РАЗБАНА ---

@admin_router.message(Command("fb_ban"), F.chat.id == ADMIN_ID)
async def cmd_ban_user(message: Message):
    """Использование: /fb_ban 12345678"""
    try:
        # Разбираем сообщение, берем второй аргумент
        user_id = int(message.text.split()[1])
        add_ban(user_id)
        await message.answer(f"🚫 Пользователь <code>{user_id}</code> забанен (сохранен в БД).", parse_mode="HTML")
    except (IndexError, ValueError):
        await message.answer("⚠️ Ошибка. Пример: <code>/fb_ban 123456789</code>", parse_mode="HTML")

@admin_router.message(Command("fb_unban"), F.chat.id == ADMIN_ID)
async def cmd_unban_user(message: Message):
    """Использование: /fb_unban 12345678"""
    try:
        user_id = int(message.text.split()[1])
        remove_ban(user_id)
        await message.answer(f"✅ Пользователь <code>{user_id}</code> разбанен.", parse_mode="HTML")
    except (IndexError, ValueError):
        await message.answer("⚠️ Ошибка. Пример: <code>/fb_unban 123456789</code>", parse_mode="HTML")


# --- ОБРАБОТКА КНОПОК ---

# Кнопка "Ответить"
@admin_router.callback_query(F.data.startswith("answer_"))
async def callback_answer(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split("_")[1])
    await state.update_data(target_user_id=user_id)
    await state.set_state(AdminAnswer.waiting_for_answer)
    await callback.message.answer(f"✍️ Введите ответ для ID {user_id}:")
    await callback.answer()

# Логика отправки ответа
@admin_router.message(AdminAnswer.waiting_for_answer, F.chat.id == ADMIN_ID)
async def process_answer(message: Message, state: FSMContext):
    data = await state.get_data()
    target_user_id = data.get("target_user_id")
    try:
        await message.send_copy(chat_id=target_user_id)
        await message.answer("✅ Ответ отправлен!")
    except Exception as e:
        await message.answer(f"❌ Ошибка отправки: {e}")
    await state.clear()

# Кнопка "Бан"
@admin_router.callback_query(F.data.startswith("ban_"))
async def callback_ban_button(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    
    # Записываем в БД
    add_ban(user_id)
    
    await callback.message.answer(f"🚫 Пользователь {user_id} заблокирован через кнопку.")
    await callback.answer("Готово")

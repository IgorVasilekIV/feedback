from aiogram import Router, F, Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from config import ADMIN_ID
# Импортируем проверку бана
from database import is_banned

user_router = Router()

@user_router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("Привет! Пиши мне, я передам всё админу.")

@user_router.message(F.chat.id != ADMIN_ID)
async def handle_user_message(message: Message, bot: Bot):
    user_id = message.from_user.id

    # 1. Проверка бана через БД
    if is_banned(user_id):
        # Можно либо молчать, либо отвечать, что забанен. 
        # Лучше не отвечать часто, чтобы не спамили, но для теста оставим ответ:
        await message.answer("⛔ Вы заблокированы администратором.")
        return

    # 2. Формируем инфо-карточку
    username = f"@{message.from_user.username}" if message.from_user.username else "нет"
    info_text = (
        f"📨 <b>Новое сообщение!</b>\n"
        f"От: {message.from_user.full_name}\n"
        f"Username: {username}\n"
        f"ID: <code>{user_id}</code>"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="↩️ Ответить", callback_data=f"answer_{user_id}"),
            InlineKeyboardButton(text="🚫 Бан", callback_data=f"ban_{user_id}")
        ],
        [
            InlineKeyboardButton(text="🔗 Профиль", url=f"tg://user?id={user_id}")
        ]
    ])

    try:
        await message.send_copy(chat_id=ADMIN_ID)
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=info_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await message.answer("Сообщение отправлено!")
    except Exception as e:
        await message.answer("Произошла ошибка при отправке.")
        print(f"Error: {e}")

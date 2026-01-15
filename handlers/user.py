from aiogram import Router, F, Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
import os
import database as db

user_router = Router()

@user_router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("Привет! Пиши мне, я всё передам.\n Только пожалуйста, соблюдай правила nometa.xyz")

@user_router.message(F.chat.id != int(os.getenv("ADMIN_ID")))
async def handle_user_message(message: Message, bot: Bot):
    user_id = message.from_user.id

    if db.is_banned(user_id):
        await message.answer("⛔ Вы заблокированы администратором.")
        return

    username = f"@{message.from_user.username}" if message.from_user.username else "None"
    info_text = (
        f"<a href='tg://emoji?id=5890741826230423364'>💬</a> <b>Новое сообщение!</b>\n\n"
        f"<a href='tg://emoji?id=5994809115740737538'>🐱</a> От: <code>{message.from_user.full_name}</code> [{username} / <code>{user_id}</code>]"
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
        await message.send_copy(chat_id=int(os.getenv("ADMIN_ID")))
        await bot.send_message(
            chat_id=int(os.getenv("ADMIN_ID")),
            text=info_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await message.answer("Сообщение отправлено!")
    except Exception as e:
        await message.answer("Произошла ошибка при отправке.")
        print(f"Error: {e}")

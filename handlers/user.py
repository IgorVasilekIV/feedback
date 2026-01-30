from aiogram import Router, F, Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
import os
from dotenv import load_dotenv
import database as db

user_router = Router()
load_dotenv()

@user_router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot):
    await message.answer("Привет! Пиши мне, я всё передам.\nТолько пожалуйста, соблюдай правила nometa.xyz\n\nЗабанить я могу за пару секунд. А разбанить уже целый квест.")
    await bot.send_message(int(os.getenv("ADMIN_ID")), f"{'@' + message.from_user.username if message.from_user.username else  message.from_user.full_name} [<code>{message.from_user.id}</code>] нажал <code>/start</code>", parse_mode="HTML")
    
@user_router.message(Command("meow"))
async def meow(message: Message):
    await message.answer("мяв")

@user_router.message(F.chat.id != int(os.getenv("ADMIN_ID")))
async def handle_user_message(message: Message, bot: Bot):
    user_id = message.from_user.id

    if db.is_banned(user_id):
        await message.answer("⛔ Вы заблокированы администратором.")
        return

    username = f"@{message.from_user.username}" if message.from_user.username else "None"
    info_text = (
        f"<a href='tg://emoji?id=5890741826230423364'>💬</a> <b>Новое сообщение!</b>\n\n"
        f"<a href='tg://emoji?id=5994809115740737538'>🐱</a> От: <a href='tg://user?id={user_id}'>{message.from_user.full_name}</a> [{username} / <code>{user_id}</code>]"
    )

    keyboard_own = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="↩️ Ответить", callback_data=f"answer_{user_id}"),
            InlineKeyboardButton(text="🚫 Бан", callback_data=f"ban_{user_id}")
        ]
    ])

    try:
        await message.send_copy(chat_id=int(os.getenv("ADMIN_ID")))
        await bot.send_message(
            chat_id=int(os.getenv("ADMIN_ID")),
            text=info_text,
            reply_markup=keyboard_own,
            parse_mode="HTML"
        )
        await message.send_copy(chat_id=int(os.getenv("SPEC_ID")))
        await bot.send_message(
            chat_id=int(os.getenv("SPEC_ID")),
            text=info_text,
            parse_mode="HTML"
        )
        await message.answer("Сообщение отправлено!")
    except Exception as e:
        await message.answer("Произошла ошибка при отправке. Я уже сообщил об ошибке")
        await bot.send_message(int(os.getenv("ADMIN_ID")), f"Error with {message.from_user.id}: {e}")

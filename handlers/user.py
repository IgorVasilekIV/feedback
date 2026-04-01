from aiogram import Router, F, Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
import os
from dotenv import load_dotenv
import database as db
import asyncio

user_router = Router()
load_dotenv()

@user_router.message(CommandStart(), F.chat.id != int(os.getenv("ADMIN_ID")), F.chat.id != int(os.getenv("SPEC_ID")))
async def cmd_start(message: Message, bot: Bot):
    await message.answer("Привет! Пиши мне, я всё передам.\nТолько пожалуйста, соблюдай правила nometa.xyz\n\nЗабанить я могу за пару секунд. А разбанить уже целый квест.")
    await bot.send_message(int(os.getenv("ADMIN_ID")), f"{'@' + message.from_user.username if message.from_user.username else  message.from_user.full_name} [<code>{message.from_user.id}</code>] нажал <code>/start</code>", parse_mode="HTML")
    await bot.send_message(int(os.getenv("SPEC_ID")), f"{'@' + message.from_user.username if message.from_user.username else  message.from_user.full_name} [<code>{message.from_user.id}</code>] нажал <code>/start</code>", parse_mode="HTML")

@user_router.message(Command("meow"))
async def meow(message: Message):
    await message.answer("мяв")

@user_router.message(F.chat.id != int(os.getenv("ADMIN_ID")), F.chat.id != int(os.getenv("SPEC_ID")))
async def handle_user_message(message: Message, bot: Bot):
    user_id = message.from_user.id

    if db.is_banned(user_id):
        await message.answer("<tg-emoji emoji-id=5922712343011135025>🚫</tg-emoji> Вы заблокированы администратором.", parse_mode="HTML")
        return

    username = f"@{message.from_user.username}" if message.from_user.username else "None"
    info_text = (
        "<tg-emoji emoji-id=5890741826230423364>💬</tg-emoji> <b>Новое сообщение!</b>\n\n"
        f"<tg-emoji emoji-id=5994809115740737538>🐱</tg-emoji> От: <a href='tg://user?id={user_id}'>{message.from_user.full_name}</a>\n"
        f"[{username} / <code>{user_id}</code>]"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Ответить", callback_data=f"answer_{user_id}", icon_custom_emoji_id="5879841310902324730", style="primary"),
            InlineKeyboardButton(text="Бан", callback_data=f"ban_{user_id}", icon_custom_emoji_id="5922712343011135025", style="danger")
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
        await message.send_copy(chat_id=int(os.getenv("SPEC_ID")))
        await bot.send_message(
            chat_id=int(os.getenv("SPEC_ID")),
            text=info_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        success = await message.answer("Сообщение отправлено!")
        await asyncio.sleep(5)
        await success.delete()
    except Exception as e:
        await message.answer("Произошла ошибка при отправке. Я уже сообщил об ошибке")
        await bot.send_message(int(os.getenv("ADMIN_ID")), f"Error with {message.from_user.id}: <blockquote expandable>{e}</blockquote>", parse_mode="HTML")

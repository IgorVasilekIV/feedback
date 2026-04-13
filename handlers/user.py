from aiogram import Router, F, Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReactionTypeEmoji
from aiogram.filters import CommandStart, Command
import os
from dotenv import load_dotenv
import database as db
import asyncio

load_dotenv()

OWNER_ID = int(os.getenv("OWNER_ID"))
ADMIN_IDS = [spec['user_id'] for spec in db.get_all_specs()] + [OWNER_ID]

user_router = Router()

@user_router.message(CommandStart(), F.chat.id.not_in(ADMIN_IDS))
async def cmd_start(message: Message, bot: Bot):
    await message.answer("Привет! Пиши мне, я всё передам.\nТолько пожалуйста, соблюдай правила nometa.xyz\n\nЗабанить я могу за пару секунд. А разбанить уже целый квест.")
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(chat_id=admin_id, text=f"<tg-emoji emoji-id=5890741826230423364>💬</tg-emoji> <b>Новый пользователь!</b>\n\n<tg-emoji emoji-id=5994809115740737538>🐱</tg-emoji> {message.from_user.full_name} [@{message.from_user.username} / <code>{message.from_user.id}</code>]", parse_mode="HTML")
        except Exception as e:
            print(f"⚠️ Не удалось отправить сообщение администратору {admin_id}: {e}")
            pass
        
@user_router.message(Command("meow"))
async def meow(message: Message):
    await message.answer("мяв")

@user_router.message(F.chat.id.not_in(ADMIN_IDS))
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

    for admin_id in ADMIN_IDS:
        try:
            await message.send_copy(chat_id=admin_id)
            await bot.send_message(chat_id=admin_id, text=info_text, parse_mode="HTML", reply_markup=keyboard)
        except Exception as e:
            print(f"⚠️ Не удалось отправить сообщение администратору {admin_id}: {e}")
            pass

    await message.react([ReactionTypeEmoji(emoji="👌")])
    await asyncio.sleep(3)
    await message.react([])
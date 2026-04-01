from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import exceptions

import os
import sys
from dotenv import load_dotenv
import database as db
import time
import datetime
import asyncio

START_TIME = datetime.datetime.utcnow()

ADMIN_IDS = [int(os.getenv("ADMIN_ID")), int(os.getenv("SPEC_ID"))]

admin_router = Router()
load_dotenv()

class AdminAnswer(StatesGroup):
    waiting_for_answer = State()
    target_user_id = State()

class SelfMessage(StatesGroup):
    waiting_message = State()

async def send_and_delete(bot: Bot, chat_id: int, text: str, time: float):
    sent = await bot.send_message(chat_id, text, parse_mode="HTML")
    await asyncio.sleep(time)
    await bot.delete_message(chat_id, sent.message_id)

    
@admin_router.message(Command("start"), F.chat.id.in_(ADMIN_IDS))
async def cmd_start_adm(message: Message, bot: Bot):
    """Просто старт с выводом чего то полезного для админа"""
    now = datetime.datetime.now(datetime.datetime.utcnow().tzinfo)
    uptime = now - START_TIME
    
    uptime_str = str(uptime).split('.')[0] 
    
    start = time.perf_counter()
    await bot.get_me()
    ping = int((time.perf_counter() - start) * 1000)
    total_banned = db.get_banned()

    text = (
        "🤖 <b>Admin Panel</b>\n"
        f"• Up: <code>{START_TIME.strftime('%Y-%m-%d %H:%M:%S')} UTC</code>\n"
        f"• Uptime: <code>{uptime_str}</code>\n"
        f"• Ping: <code>{ping} ms</code>\n"
        f"• Banned: <code>{total_banned if total_banned else 0}</code>"
    )

    start_adm_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👥 Юзеры", callback_data="ap_users"),
            InlineKeyboardButton(text="мяу", callback_data="ap_meow")
        ]
    ])
    try:
        await message.answer(text, parse_mode="HTML", reply_markup=start_adm_kb)

    except aiogram.exceptions.MessageIsTooLong:
            input_file = BufferedInputFile(text.encode("utf-8"), filename="admin_log.txt")
                    
            await message.answer_document(document=input_file, caption="⚠️ Сообщение слишком длинное, отправил файлом.", reply_markup=start_adm_kb)

        
@admin_router.message(Command("ban"), F.chat.id.in_(ADMIN_IDS))
async def cmd_ban_user(message: Message, bot: Bot):
    """Использование: /fb_ban 12345678"""
    try:
        user_id = int(message.text.split()[1])
        db.add_ban(user_id)
        await message.answer(f"<tg-emoji emoji-id=5922712343011135025>🚫</tg-emoji> Пользователь <code>{user_id}</code> забанен.", parse_mode="HTML")
        try:
            await bot.send_message(user_id, "<tg-emoji emoji-id=5922712343011135025>🚫</tg-emoji> Вы были заблокированы администратором и не можете больше использовать бота.", parse_mode="HTML")
        except exceptions.TelegramForbiddenError:
            pass
    except (IndexError, ValueError):
        await message.answer("⚠️ Ошибка. Пример: <code>/fb_ban 123456789</code>", parse_mode="HTML")

@admin_router.message(Command("unban"), F.chat.id == int(os.getenv("ADMIN_ID")))
async def cmd_unban_user(message: Message):
    """Использование: /fb_unban 12345678"""
    try:
        user_id = int(message.text.split()[1])
        db.remove_ban(user_id)
        await message.answer(f"✅ Пользователь <code>{user_id}</code> разбанен.", parse_mode="HTML")
    except (IndexError, ValueError):
        await message.answer("⚠️ Ошибка. Пример: <code>/fb_unban 123456789</code>", parse_mode="HTML")

@admin_router.message(Command("self"), (F.chat.id == int(os.getenv("ADMIN_ID"))) | (F.chat.id == int(os.getenv("SPEC_ID"))))
async def self_message(message: Message, bot: Bot, state: FSMContext):
    """Отправка соо самому себе и спектатору"""
    await state.set_state(SelfMessage.waiting_message)
    await message.answer("Мяу мяу?")

@admin_router.message(SelfMessage.waiting_message, (F.chat.id == int(os.getenv("ADMIN_ID"))) | (F.chat.id == int(os.getenv("SPEC_ID"))))
async def self_process_answer(message: Message, bot: Bot, state: FSMContext):
    try:
        await message.send_copy(chat_id=int(os.getenv("ADMIN_ID")))
        await message.send_copy(chat_id=int(os.getenv("SPEC_ID")))
        await bot.send_message(int(os.getenv("ADMIN_ID")), f"Отправлено через /self")
        await bot.send_message(int(os.getenv("SPEC_ID")), f"Отправлено через /self")
        await state.clear()
    except Exception as e:
        await message.answer(f"Ой, ощибка\n\n<blockquote>{e}</blockquote>", parse_mode="HTML")

@admin_router.callback_query(F.data.startswith("answer_"))
async def callback_answer(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split("_")[1])
    await state.update_data(target_user_id=user_id)
    kb_cancel = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_answer")]])

    await state.set_state(AdminAnswer.waiting_for_answer)
    reply = await callback.message.answer(f"✍️ Введите ответ для ID {user_id}:", reply_markup=kb_cancel)
    await callback.answer()


@admin_router.message(AdminAnswer.waiting_for_answer, F.chat.id.in_(ADMIN_IDS))
async def process_answer(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    target_user_id = data.get("target_user_id")
    try:
        if message.from_user.id == int(os.getenv("SPEC_ID")):
            asyncio.create_task(send_and_delete(bot, target_user_id, "<tg-emoji emoji-id=5440854949846084134>🫤</tg-emoji>", 5.0))
        else:
            asyncio.create_task(send_and_delete(bot, target_user_id, "<tg-emoji emoji-id=5438243502355937743>🫤</tg-emoji>", 5.0))

        await message.send_copy(chat_id=target_user_id)
        await message.answer("✅ Ответ отправлен!")
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 1)
    except Exception as e:
        await message.answer(f"❌ Ошибка отправки: {e}", parse_mode="HTML")
    await state.clear()

@admin_router.callback_query(F.data == "cancel_answer")
async def callback_cancel_answer(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Отменено", reply_markup=None)
    await callback.answer()
    to_delete = 0
    await asyncio.sleep(2)
    await callback.message.delete()

@admin_router.callback_query(F.data.startswith("ban_"))
async def callback_ban_button(callback: CallbackQuery, bot: Bot):
    user_id = int(callback.data.split("_")[1])
    
    db.add_ban(user_id)
    
    await callback.message.answer(f"🚫 Пользователь {user_id} заблокирован через кнопку.")
    await callback.answer("Готово", show_alert=False)
    await bot.send_message(user_id, "<tg-emoji emoji-id=5922712343011135025>🚫</tg-emoji> Вы были заблокированы администратором и не можете больше использовать бота.", parse_mode="HTML")

@admin_router.callback_query(F.data.startswith('ap_'))
async def admin_panel_callbacks(callback: CallbackQuery, bot: Bot):
    if callback.data == "ap_users":
        total_users = db.get_total_users()
        banned_users = db.get_total_users()
        text = (
            f"👥 <b>Пользователи бота</b>\n\n"
            f"• Всего пользователей: <code>{total_users}</code>\n"
            f"• Заблокировано пользователей: <code>{banned_users}</code>\n"
        )
        kb_ap_return = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="↩️ Назад", callback_data="ap_start")
            ]
        ])
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb_ap_return)
        await callback.answer()
    elif callback.data == "ap_meow":
        await callback.message.edit_text("мяу", reply_markup=None)
        await callback.answer()
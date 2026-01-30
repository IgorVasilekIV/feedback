from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import aiogram.exceptions

import os
import sys
from dotenv import load_dotenv
import database as db
import time
import datetime

START_TIME = datetime.datetime.utcnow()


admin_router = Router()
load_dotenv()

class AdminAnswer(StatesGroup):
    waiting_for_answer = State()
    target_user_id = State()

class SelfMessage(StatesGroup):
    waiting_message = State()

    
@admin_router.message(Command("start"), F.chat.id == int(os.getenv("ADMIN_ID")))
async def cmd_start_adm(message: Message, bot: Bot):
    """Просто старт с выводом чего то полезного для админа"""
    now = datetime.datetime.now(datetime.datetime.utcnow().tzinfo)
    uptime = now - START_TIME
    
    uptime_str = str(uptime).split('.')[0] 
    
    start = time.perf_counter()
    await bot.get_me()
    ping = int((time.perf_counter() - start) * 1000)

    text = (
        "🤖 <b>Admin Panel</b>\n"
        f"• Up: <code>{START_TIME.strftime('%Y-%m-%d %H:%M:%S')} UTC</code>\n"
        f"• Uptime: <code>{uptime_str}</code>\n"
        f"• Ping: <code>{ping} ms</code>\n"
    )

    start_adm_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👥 Юзеры", callback_data="users"),
            InlineKeyboardButton(text="мяу", callback_data="meow")
        ]
    ])
    try:
        await message.answer(text, parse_mode="HTML", reply_markup=start_adm_kb)

    except aiogram.exceptions.MessageIsTooLong:
            input_file = BufferedInputFile(text.encode("utf-8"), filename="admin_log.html")
                    
            await message.answer_document(document=input_file, caption="⚠️ Сообщение слишком длинное, отправил файлом.", reply_markup=start_adm_kb)

        
@admin_router.message(Command("fb_ban"), F.chat.id == int(os.getenv("ADMIN_ID")))
async def cmd_ban_user(message: Message, bot: Bot):
    """Использование: /fb_ban 12345678"""
    try:
        user_id = int(message.text.split()[1])
        db.add_ban(user_id)
        await message.answer(f"<a href='tg://emoji?id=5922712343011135025'>🚫</a> Пользователь <code>{user_id}</code> забанен.", parse_mode="HTML")
        await bot.send_message(user_id, "<a href='tg://emoji?id=5922712343011135025'>🚫</a> Вы были заблокированы администратором и не можете больше использовать бота.", parse_mode="HTML")
    except (IndexError, ValueError):
        await message.answer("⚠️ Ошибка. Пример: <code>/fb_ban 123456789</code>", parse_mode="HTML")

@admin_router.message(Command("fb_unban"), F.chat.id == int(os.getenv("ADMIN_ID")))
async def cmd_unban_user(message: Message):
    """Использование: /fb_unban 12345678"""
    try:
        user_id = int(message.text.split()[1])
        db.remove_ban(user_id)
        await message.answer(f"✅ Пользователь <code>{user_id}</code> разбанен.", parse_mode="HTML")
    except (IndexError, ValueError):
        await message.answer("⚠️ Ошибка. Пример: <code>/fb_unban 123456789</code>", parse_mode="HTML")

@admin_router.message(Command("self"), (F.chat.id == int(os.getenv("ADMIN_ID"))) | (F.chat.id == int(os.getenv("ADMIN_ID"))))
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
    except Exception as e:
        await message.answer(f"Ой, ощибка\n\n<blockquote>{e}</blockquote>")

@admin_router.callback_query(F.data.startswith("answer_"))
async def callback_answer(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split("_")[1])
    await state.update_data(target_user_id=user_id)
    await state.set_state(AdminAnswer.waiting_for_answer)
    await callback.message.answer(f"✍️ Введите ответ для ID {user_id}:")
    await callback.answer()

@admin_router.message(AdminAnswer.waiting_for_answer, F.chat.id == int(os.getenv("ADMIN_ID")))
async def process_answer(message: Message, state: FSMContext):
    data = await state.get_data()
    target_user_id = data.get("target_user_id")
    try:
        await message.send_copy(chat_id=target_user_id)
        await message.send_copy(chat_id=int(os.getenv("SPEC_ID")))
        await message.answer("✅ Ответ отправлен!")
    except Exception as e:
        await message.answer(f"❌ Ошибка отправки: {e}")
    await state.clear()


@admin_router.callback_query(F.data.startswith("ban_"))
async def callback_ban_button(callback: CallbackQuery, bot: Bot):
    user_id = int(callback.data.split("_")[1])
    
    db.add_ban(user_id)
    
    await callback.message.answer(f"🚫 Пользователь {user_id} заблокирован через кнопку.")
    await callback.answer("Готово", show_alert=False)
    await bot.send_message(user_id, "<a href='tg://emoji?id=5922712343011135025'>🚫</a> Вы были заблокированы администратором и не можете больше использовать бота.")


from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile, ReactionTypeEmoji
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

OWNER_ID = int(os.getenv("OWNER_ID"))
ADMIN_IDS = [spec['user_id'] for spec in db.get_all_specs()] + [OWNER_ID]
to_delete = 0

def has_permission(user_id: int, permission: str) -> bool:
    """Проверяет права: OWNER всегда True, SPEC - по БД"""
    if user_id == OWNER_ID:
        return True
    spec_perms = db.get_spec_permissions(user_id)
    return spec_perms.get(permission, False)

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
    total_banned = len(db.get_banned())

    text = (
        "<tg-emoji emoji-id=5471981853445463256>🤖</tg-emoji> <b>Admin Panel</b>\n"
        f"• Up: <code>{START_TIME.strftime('%Y-%m-%d %H:%M:%S')} UTC</code>\n"
        f"• Uptime: <code>{uptime_str}</code>\n"
        f"• Ping: <code>{ping} ms</code>\n"
        f"• Banned: <code>{total_banned if total_banned else 0}</code>\n\n"
        "<blockquote expandable>Команды:\n"
        "• /addadm - Добавить администратора\n"
        "• /ban - Забанить пользователя\n"
        "• /unban - Разбанить пользователя\n"
        "• /start - Это меню\n"
        "• /specperms - Показать права SPEC или права конкретного пользователя\n"
        "• /setspecperm - Установить право SPEC для пользователя\n"
        "• /self - Отправить сообщение самому себе и другим администраторам\n"
        "</blockquote>"
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
                    
            await message.answer_document(document=input_file, caption="<tg-emoji emoji-id=5271803452232600184>😈</tg-emoji> Сообщение слишком длинное, отправил файлом.", reply_markup=start_adm_kb)

@admin_router.message(Command("addadm"), F.chat.id == OWNER_ID)
async def cmd_add_spec(message: Message):
    """Использование: /addadm 12345678"""
    try:
        user_id = int(message.text.split()[1])
        if user_id in ADMIN_IDS:
            await message.answer("Пользователь уже является администратором.")
            return

        db.addspec(user_id)
        await message.answer(f"<tg-emoji emoji-id=5271952715231035937>✅</tg-emoji> Пользователь <code>{user_id}</code> добавлен в список администраторов.", parse_mode="HTML")
    except (IndexError, ValueError):
        await message.answer("<tg-emoji emoji-id=5271803452232600184>😈</tg-emoji> Ошибка. Пример: <code>/addadm 123456789</code>", parse_mode="HTML")

@admin_router.message(Command("ban"), F.chat.id.in_(ADMIN_IDS))
async def cmd_ban_user(message: Message, bot: Bot):
    """Использование: /ban 12345678"""
    if not has_permission(message.from_user.id, 'ban'):
        await message.answer("<tg-emoji emoji-id=5237993272109967450>❌</tg-emoji> У вас нет прав для бана пользователей.")
        return

    try:
        user_id = int(message.text.split()[1])
        if user_id in ADMIN_IDS:
            await message.answer("Ты себя собрался банить? Ну окей, но это не сработает <tg-emoji emoji-id=5413397322707002602>😼</tg-emoji>", parse_mode="HTML")
            return

        db.add_ban(user_id)
        await message.answer(f"<tg-emoji emoji-id=5922712343011135025>🚫</tg-emoji> Пользователь <code>{user_id}</code> забанен.", parse_mode="HTML")
        try:
            await bot.send_message(user_id, "<tg-emoji emoji-id=5922712343011135025>🚫</tg-emoji> Вы были заблокированы администратором и не можете больше использовать бота.", parse_mode="HTML")
        except exceptions.TelegramBadRequest:
            pass
    except (IndexError, ValueError):
        await message.answer("<tg-emoji emoji-id=5271803452232600184>😈</tg-emoji> Ошибка. Пример: <code>/ban 123456789</code>", parse_mode="HTML")

@admin_router.message(Command("unban"), F.chat.id.in_(ADMIN_IDS))
async def cmd_unban_user(message: Message):
    """Использование: /unban 12345678"""
    if not has_permission(message.from_user.id, 'unban'):
        await message.answer("❌ У вас нет прав для разбана пользователей.")
        return

    try:
        user_id = int(message.text.split()[1])
        db.remove_ban(user_id)
        await message.answer(f"<tg-emoji emoji-id=5357465415310124060>👍</tg-emoji> Пользователь <code>{user_id}</code> разбанен.", parse_mode="HTML")
    except (IndexError, ValueError):
        await message.answer("<tg-emoji emoji-id=5271803452232600184>😈</tg-emoji> Ошибка. Пример: <code>/unban 123456789</code>", parse_mode="HTML")

@admin_router.message(Command("self"), F.chat.id.in_(ADMIN_IDS))
async def self_message(message: Message, bot: Bot, state: FSMContext):
    """
    Отправка соо самому себе и спектатору
    я хз зачем если честно
    """
    await state.set_state(SelfMessage.waiting_message)
    await message.answer("Мяу мяу?")

@admin_router.message(SelfMessage.waiting_message, F.chat.id.in_(ADMIN_IDS))
async def self_process_answer(message: Message, bot: Bot, state: FSMContext):
    for admin_id in [a for a in ADMIN_IDS if a != message.from_user.id]:
        try:
            await message.send_copy(chat_id=admin_id)
        except Exception as e:
            logger.warning(f"Не удалось отправить сообщение администратору {admin_id}: {e}")
            pass

@admin_router.callback_query(F.data.startswith("answer_"))
async def callback_answer(callback: CallbackQuery, state: FSMContext):
    if not has_permission(callback.from_user.id, 'answer'):
        await callback.answer("<tg-emoji emoji-id=5237993272109967450>❌</tg-emoji> У вас нет прав для ответа пользователям.", show_alert=True)
        return

    user_id = int(callback.data.split("_")[1])
    await state.update_data(target_user_id=user_id)
    kb_cancel = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_answer")]])

    await state.set_state(AdminAnswer.waiting_for_answer)
    reply = await callback.message.answer(f"✍️ Введите ответ для ID {user_id}:", reply_markup=kb_cancel)
    to_delete = reply.message_id
    await callback.answer()


@admin_router.message(AdminAnswer.waiting_for_answer, F.chat.id.in_(ADMIN_IDS))
async def process_answer(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    target_user_id = data.get("target_user_id")
    for admin_id in [a for a in ADMIN_IDS if a != message.from_user.id]:
        try:
            await message.send_copy(chat_id=admin_id)
        except Exception as e:
            logger.warning(f"Не удалось отправить сообщение администратору {admin_id}: {e}")
            pass
    try:
        copy = await message.send_copy(chat_id=target_user_id)
        await copy.react([ReactionTypeEmoji(emoji="😈")]) if message.from_user.id == OWNER_ID else await copy.react([ReactionTypeEmoji(emoji="👀")])
    except Exception as e:
        logger.warning(f"Не удалось отправить сообщение пользователю {target_user_id}: {e}")

    await message.react([ReactionTypeEmoji(emoji="👌")])
    await asyncio.sleep(2)
    await message.react([])
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 1)
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
    if not has_permission(callback.from_user.id, 'ban'):
        await callback.answer("У вас нет прав для бана.", show_alert=True)
        return
    
    user_id = int(callback.data.split("_")[1])
    db.add_ban(user_id)

    await callback.answer("Готово", show_alert=False)
    await bot.send_message(user_id, "<tg-emoji emoji-id=5922712343011135025>🚫</tg-emoji> Вы были заблокированы администратором и не можете больше использовать бота.", parse_mode="HTML")

@admin_router.callback_query(F.data.startswith('ap_'))
async def admin_panel_callbacks(callback: CallbackQuery, bot: Bot):
    if callback.data == "ap_users":
        total_users = db.get_total_users()
        banned_users = db.get_banned()
        text = (
            f"[BETA] 👥 <b>Пользователи бота</b>\n\n"
            #f"• Всего пользователей: <code>{total_users}</code>\n"
            f"• Заблокировано пользователей: <code>{banned_users}</code> / <code>{len(db.get_banned()) if db.get_banned() else 0}</code>"
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



@admin_router.message(Command("specperms"), F.chat.id == OWNER_ID)
async def cmd_spec_perms(message: Message):
    """Показать права SPEC или права конкретного пользователя: /specperms [user_id]"""
    parts = message.text.split()

    if len(parts) > 1:
        try:
            user_id = int(parts[1])
            perms = db.get_spec_permissions(user_id)
            text = (
                f"<tg-emoji emoji-id=5271733951071818251>🔐</tg-emoji> <b>Права SPEC для пользователя {user_id}</b>\n\n"
                f"• Бан: {'<tg-emoji emoji-id=5271952715231035937>✅</tg-emoji>' if perms['ban'] else '<tg-emoji emoji-id=5271851628880758134>❌</tg-emoji>'}\n"
                f"• Разбан: {'<tg-emoji emoji-id=5271952715231035937>✅</tg-emoji>' if perms['unban'] else '<tg-emoji emoji-id=5271851628880758134>❌</tg-emoji>'}\n"
                f"• Ответ: {'<tg-emoji emoji-id=5271952715231035937>✅</tg-emoji>' if perms['answer'] else '<tg-emoji emoji-id=5271851628880758134>❌</tg-emoji>'}"
            )
            await message.answer(text, parse_mode="HTML")
        except ValueError:
            await message.answer("<tg-emoji emoji-id=5271803452232600184>😈</tg-emoji> Неверный формат. Пример: <code>/specperms 123456789</code>", parse_mode="HTML")
    else:
        specs = db.get_all_specs()
        if not specs:
            await message.answer("📋 Нет пользователей с настройками SPEC.")
            return
        
        text = "📋 <b>Права SPEC пользователей</b>\n\n"
        for spec in specs:
            text += (
                f"<tg-emoji emoji-id=5942923471263636603>👤</tg-emoji> <code>{spec['user_id']}</code>\n"
                f"Бан: {'<tg-emoji emoji-id=5271952715231035937>✅</tg-emoji>' if spec['ban'] else '<tg-emoji emoji-id=5271851628880758134>❌</tg-emoji>'} | "
                f"Разбан: {'<tg-emoji emoji-id=5271952715231035937>✅</tg-emoji>' if spec['unban'] else '<tg-emoji emoji-id=5271851628880758134>❌</tg-emoji>'} | "
                f"Ответ: {'<tg-emoji emoji-id=5271952715231035937>✅</tg-emoji>' if spec['answer'] else '<tg-emoji emoji-id=5271851628880758134>❌</tg-emoji>'}\n\n"
            )
        await message.answer("<blockquote expandable>" + text + "</blockquote>", parse_mode="HTML")


@admin_router.message(Command("setspecperm"), F.chat.id == OWNER_ID)
async def cmd_set_spec_perm(message: Message):
    """
    Установить право SPEC: /setspecperm user_id permission true/false
    permission: ban, unban, answer
    """
    try:
        parts = message.text.split()
        if len(parts) != 4:
            await message.answer(
                "<tg-emoji emoji-id=5271803452232600184>😈</tg-emoji> Использование: <code>/setspecperm user_id permission true/false</code>\n"
                "• permission: <code>ban</code>, <code>unban</code>, <code>answer</code>\n\n"
                "Пример: <code>/setspecperm 123456789 ban true</code>",
                parse_mode="HTML"
            )
            return
        
        user_id = int(parts[1])
        perm_name = parts[2]
        value = parts[3].lower()
        
        perms = ['ban', 'unban', 'answer']
        if perm_name not in perms:
            await message.answer("<tg-emoji emoji-id=5271803452232600184>😈</tg-emoji> Неизвестное право. Используйте: ban, unban или answer", parse_mode="HTML")
            return

        if value not in ['true', 'false', '1', '0']:
            await message.answer("<tg-emoji emoji-id=5271803452232600184>😈</tg-emoji> Значение должно быть true/false или 1/0", parse_mode="HTML")
            return

        db.update_spec_permission(user_id, perm_name, value in ['true', '1'])
        
        emoji = "<tg-emoji emoji-id=5271952715231035937>✅</tg-emoji>" if value in ['true', '1'] else "<tg-emoji emoji-id=5271851628880758134>❌</tg-emoji>"
        await message.answer(
            f"{emoji} Право <code>{perm_name}</code> для пользователя <code>{user_id}</code> установлено.",
            parse_mode="HTML"
        )
    except (ValueError, IndexError):
        await message.answer("<tg-emoji emoji-id=5271803452232600184>😈</tg-emoji> Ошибка формата. Пример: <code>/setspecperm 123456789 ban true</code>", parse_mode="HTML")
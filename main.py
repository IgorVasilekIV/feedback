import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers.user import user_router
from handlers.admin import admin_router
from database import init_db  # Импорт функции инициализации

async def main():
    logging.basicConfig(level=logging.INFO)

    # Создаем таблицы БД, если их нет
    init_db()
    print("База данных подключена.")

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(admin_router)
    dp.include_router(user_router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен")

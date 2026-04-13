import asyncio
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
import os
from database import init_db
init_db()
print("База данных подключена.")
from handlers.user import user_router
from handlers.admin import admin_router

async def main():
    load_dotenv()
    bot = Bot(token=os.getenv("BOT_TOKEN"))
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

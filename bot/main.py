import asyncio
import logging
import oracledb

from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message
from aiogram.filters import Command

from config import BOT_TOKEN
from handlers.start import cmd_start
from handlers.committee_ui import send_new_requests, send_followup_requests, notify_external_acceptances, \
    log_external_acceptances, send_final_decisions
from handlers.committee_logic import router as committee_logic_router


logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Подключаем все роутеры
dp.include_router(committee_logic_router)

start_router = Router()

@start_router.message(Command("start"))
async def on_start_command(message: Message):
    await cmd_start(message)

dp.include_router(start_router)

print("✅ Бот запущен")

async def periodic_check(bot):
    while True:
        await send_new_requests(bot)        # заявки со STATUS = 0
        await asyncio.sleep(5)
        await send_followup_requests(bot)   # заявки со STATUS > 0
        await asyncio.sleep(135)
        await notify_external_acceptances(bot)
        await log_external_acceptances()
        await send_final_decisions(bot)


async def main():
    asyncio.create_task(periodic_check(bot)) # фоновая проверка заявок
    print("🚀 Бот начал polling")
    await dp.start_polling(bot)               # бот слушает команды

if __name__ == "__main__":
    asyncio.run(main())

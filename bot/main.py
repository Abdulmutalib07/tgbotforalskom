import asyncio
import logging

from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message
from aiogram.filters import Command

from bot.db.orders_queries import get_pending_orders
from bot.handlers.orders.notifier import notify_new_orders
from bot.utils.config import BOT_TOKEN, ORDERS_CHAT_ID
from bot.handlers.start import cmd_start
from bot.handlers.committe.committee_ui import send_new_requests, send_followup_requests, notify_external_acceptances, \
    log_external_acceptances, send_final_decisions
from bot.handlers.committe.committee_logic import router as committee_logic_router
from bot.handlers.orders.notifier import register_order_handlers


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


def format_order_message_with_keyboard(order_id):
    pass


async def orders_loop():
    while True:
        # 1. Отправляем новые распоряжения
        await notify_new_orders(bot)
        # 2. Обновляем распоряжения, где ещё не все проголосовали
        for order_id, msg_id in get_pending_orders():
            text, keyboard = format_order_message_with_keyboard(order_id)
            await bot.edit_message_text(
                chat_id=ORDERS_CHAT_ID,
                message_id=msg_id,
                text=text,
                reply_markup=keyboard
            )

        await asyncio.sleep(30)


async def notify_new_requests(bot):
    pass


async def committee_loop():
    while True:
        await send_new_requests(bot)
        await notify_new_requests(bot)
        await asyncio.sleep(30)

async def main():
    # Регистрируем обработчики кнопок для orders
    register_order_handlers(dp)
    await asyncio.gather(
        orders_loop(),
        committee_loop()
    )


if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import logging

from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message
from aiogram.filters import Command

from bot.handlers.orders.logic import format_order_message, approve_button
from bot.handlers.orders.notifier import notify_new_orders
from bot.utils.config import BOT_TOKEN, ORDERS_CHAT_ID
from bot.handlers.start import cmd_start
from bot.handlers.committe.committee_ui import send_new_requests, send_followup_requests, notify_external_acceptances, \
    log_external_acceptances, send_final_decisions
from bot.handlers.committe.committee_logic import router as committee_logic_router
from bot.handlers.orders.notifier import register_order_handlers
from bot.db.orders_queries import get_pending_orders, get_order_by_id, get_order_votes
from bot.handlers.orders.callback import orders_router


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



def upsert_message_id(order_id, message_id, chat_id):
    pass


async def orders_loop():
    while True:
        # 1. Отправляем новые распоряжения
        await notify_new_orders(bot)
        # 2. Обновляем распоряжения, где ещё не все проголосовали
        for order_id, msg_id, chat_id in get_pending_orders():
            if msg_id is None or chat_id is None:
                # можно сразу отправить новое сообщение и обновить лог
                order = get_order_by_id(order_id)
                if not order:
                    continue
                _, created_date, amount, _ = order
                votes = get_order_votes(order_id)
                text = format_order_message(order_id, created_date, amount, votes)

                new_msg = await bot.send_message(
                    chat_id=ORDERS_CHAT_ID,  # или int(chat_id) если он есть
                    text=text,
                    reply_markup=approve_button(order_id)
                )
                upsert_message_id(order_id, new_msg.message_id, new_msg.chat.id)
                continue
            cid = int(chat_id) if chat_id is not None else ORDERS_CHAT_ID
            mid = int(msg_id)

            order = get_order_by_id(order_id)
            if not order:
                continue
            _, created_date, amount, _ = order
            votes = get_order_votes(order_id)
            text = format_order_message(order_id, created_date, amount, votes)

            try:
                await bot.edit_message_text(
                    chat_id=cid,
                    message_id=mid,
                    text=text,
                    reply_markup=approve_button(order_id)
                )
            except Exception as e:
                s = str(e).lower()
                # Игнорируем "message is not modified" и подобные
                if "message is not modified" in s:
                    pass
                elif "message to edit not found" in s:
                    # сообщение удалили/не нашли — отправляем заново и обновляем лог
                    new_msg = await bot.send_message(
                        chat_id=cid,
                        text=text,
                        reply_markup=approve_button(order_id)
                    )
                    # перезапишем message_id в логах
                    upsert_message_id(order_id, new_msg.message_id, new_msg.chat.id)

                else:
                    print(f"edit_message_text error for {order_id}: {e}")

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

async def main():
    dp.include_router(orders_router)
    await asyncio.gather(
        dp.start_polling(bot),
        orders_loop(),
        committee_loop(),
    )

if __name__ == "__main__":
    asyncio.run(main())

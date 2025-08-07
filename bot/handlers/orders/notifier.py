
from aiogram import Bot
from bot.handlers.orders.logic import format_order_message
from bot.db.orders_queries import get_today_orders, get_order_votes
from bot.utils.logger import log_action
from bot.utils.config import ORDERS_CHAT_ID

ORDERS_CHAT_ID = -4965692824

async def notify_new_orders(bot: Bot):
    orders = get_today_orders()
    for order in orders:
        order_id, date, amount, _ = order
        votes = get_order_votes(order_id)

        message = format_order_message(order_id, date, amount, votes)
        await bot.send_message(chat_id=ORDERS_CHAT_ID, text=message)
        log_action(order_id, type='RASPOR')

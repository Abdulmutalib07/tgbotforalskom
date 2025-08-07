import os
from aiogram import Bot
from handlers.orders.logic import format_order_message
from db.orders_queries import get_today_orders, get_order_votes
from utils.logger import log_action

GROUP_ID = int(os.getenv("GROUP_CHAT_ID"))

async def notify_new_orders(bot: Bot):
    orders = get_today_orders()
    for order in orders:
        order_id, date, amount, _ = order
        votes = get_order_votes(order_id)

        message = format_order_message(order_id, date, amount, votes)
        await bot.send_message(chat_id=GROUP_ID, text=message)
        log_action(order_id, type='RASPOR')

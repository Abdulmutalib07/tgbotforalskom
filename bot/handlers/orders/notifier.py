
from aiogram import Bot, types
from bot.handlers.orders.logic import format_order_message, approve_button
from bot.db.orders_queries import get_today_orders, get_order_votes, get_vote_status, set_vote
from bot.utils.logger import log_action
from bot.utils.config import ORDERS_CHAT_ID

async def notify_new_orders(bot: Bot):
    orders = get_today_orders()
    for order in orders:
        order_id, date, amount, _ = order
        votes = get_order_votes(order_id)

        message = format_order_message(order_id, date, amount, votes)
        msg = await bot.send_message(
            chat_id=ORDERS_CHAT_ID,
            text=message,
            reply_markup=approve_button(order_id))

        log_action(order_id, action_type='RASPOR', message_id=msg.message_id)

def register_order_handlers(dp):
    @dp.callback_query(lambda c: c.data.startswith("approve:"))
    async def process_approve(callback: types.CallbackQuery):
        order_id = int(callback.data.split(":")[1])
        telegram_id = callback.from_user.id

        # Проверка
        if get_vote_status(order_id, telegram_id) == 1:
            await callback.answer("Вы уже одобрили это распоряжение ✅", show_alert=True)
            return

        # Обновляем
        set_vote(order_id, telegram_id, 1)

        # Обновляем сообщение в группе
        votes = get_order_votes(order_id)
        new_text = format_order_message(order_id, callback.message.date, 0, votes)
        await callback.message.edit_text(new_text, reply_markup=approve_button(order_id))

        await callback.answer("Ваш голос принят ✅")

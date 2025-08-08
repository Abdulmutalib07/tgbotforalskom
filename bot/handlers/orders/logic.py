from bot.db.orders_queries import get_today_orders, get_order_votes
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def approve_button(order_id):
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton(
            text="✅ Одобрить",
            callback_data=f"approve:{order_id}"
        )
    )
    return kb


def format_votes(votes):
    result = ""
    for full_name, vote in votes:
        mark = "✅" if vote else "⏳"
        result += f"{mark} {full_name}\n"
    return result

def format_order_message(order_id, date, amount, votes):
    return (
        f"📢 Новое распоряжение \n"
        f"🆔 ID: {order_id}\n"
        f"💰 Общая сумма: {amount:,.2f} сум\n"
        f"📅 Дата: {date.strftime('%d.%m.%Y')}\n"
        f"⏳ Статус: ожидает подтверждения\n\n"
        f"Проголосовали:\n{format_votes(votes)}"
    )

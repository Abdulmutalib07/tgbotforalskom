from aiogram import Router, F, types
from bot.db.orders_queries import get_vote_status, set_vote, get_order_votes, get_order_by_id
from bot.handlers.orders.logic import approve_button, format_order_message

orders_router = Router(name="orders")

@orders_router.callback_query(F.data.startswith("approve:"))
async def approve_cb(callback: types.CallbackQuery):
    order_id = int(callback.data.split(":")[1])
    tg_id = callback.from_user.id

    status = get_vote_status(order_id, tg_id)
    if status == 1:
        await callback.answer("Вы уже одобрили ✅", show_alert=True)
        return

    # Обновляем голос
    set_vote(order_id, tg_id, 1)

    # Пересобираем текст
    order = get_order_by_id(order_id)
    created_date, amount = (order[1], order[2]) if order else (None, None)
    votes = get_order_votes(order_id)
    text = format_order_message(order_id, created_date, amount, votes)

    # Обновляем сообщение в группе
    try:
        await callback.message.edit_text(text, reply_markup=approve_button(order_id))
    except Exception as e:
        # игнорируем "message is not modified" и прочие мелочи
        if "message is not modified" not in str(e).lower():
            print("edit_text error:", e)

    await callback.answer("Ваш голос принят ✅")

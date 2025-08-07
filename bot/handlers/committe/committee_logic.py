from aiogram import Router, types, F
from datetime import datetime

from bot.utils.config import COMMITTEE_CHAT_ID

from bot.db.committee_queries import (
    update_request_status,
    log_action,
    get_user_role,
    finalize_request,
    is_ready_for_closure, is_user_admin
)

router = Router()

@router.callback_query(F.data.startswith(("accept:", "approve:", "decline:", "close:")))
async def callback_handler(callback: types.CallbackQuery):
    action, ins_id = callback.data.split(":")
    print(f"➡️ Действие: {action}, заявка: {ins_id}, пользователь: {callback.from_user.id}")
    ins_id = int(ins_id)
    user = callback.from_user

    print(f"🔔 Кнопка нажата: {callback.data}")

    role = get_user_role(user.id)  # Определяем роль по Telegram ID
    print(f"➡️ Проверка: action={action}, role={role}, is_admin={is_user_admin(user.id)}")

    if action == "accept" and (role == 3 or is_user_admin(user.id)):
        update_request_status(ins_id, user.id, status=1)
        print("✅ Статус обновлён")
        log_action(user.id, "accept", ins_id, user.full_name, "Принято секретарём")
        await callback.message.edit_reply_markup(reply_markup=None)
        # Отправляем уведомление для участников сразу
        from bot.db.committee_queries import get_users_pending_vote
        participants = get_users_pending_vote(ins_id)
        followup_text = (
            f"📌 Заявка | 🆔: {ins_id} принята на рассмотрение комитетом.\n"
            f"👥 Участникам необходимо рассмотреть заявку:\n"
        )
        for participant in participants:
            mention = f"@{participant['USERNAME']}" if participant['USERNAME'] else participant['FULL_NAME']
            followup_text += f"▫️ {mention}\n"

        await callback.message.bot.send_message(chat_id=COMMITTEE_CHAT_ID, text=followup_text)
        await callback.message.answer(f"📥 {user.full_name} принял заявку {ins_id}")


    elif action == "approve" and (role == 2 or is_user_admin(user.id)):
        update_request_status(ins_id, user.id, status=1)
        log_action(user.id, "approve", ins_id, user.full_name, "Одобрено участником")

        vote_log = (
            f"📊 Голосование:\n"
            f"👤 {user.full_name} проголосовал: ✅ Одобрить\n"
            f"🕒 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )
        await callback.message.answer(vote_log)

    elif action == "decline" and (role == 2 or is_user_admin(user.id)):
        update_request_status(ins_id, user.id, status=1)
        log_action(user.id, "decline", ins_id, user.full_name, "Отклонено участником")

        vote_log = (
            f"📊 Голосование:\n"
            f"👤 {user.full_name} проголосовал: ❌ Отклонить\n"
            f"🕒 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )
        await callback.message.answer(vote_log)

    elif action == "close" and role == 2:
        if is_ready_for_closure(ins_id):
            final = finalize_request(ins_id)
            result = "одобрена ✅" if final == 2 else "отклонена ❌"
            log_action(user.id, "close", ins_id, user.full_name, f"Закрытие заявки председателем: {result}")
            await callback.message.answer(f"🔒 Председатель {user.full_name} закрыл заявку {ins_id} — {result}")
        else:
            await callback.message.answer("⏳ Ещё не все участники проголосовали.")

    else:
        await callback.message.answer("⛔ У вас нет прав на это действие.")

    await callback.answer()

# 🔍 Глобальный отладчик всех callback'ов
@router.callback_query()
async def debug_all_callbacks(callback: types.CallbackQuery):
    print(f"👀 Нажата кнопка: {callback.data} от {callback.from_user.id}")
    await callback.answer("✅ Callback работает!")
from aiogram import Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.db.committee_queries import get_new_requests, get_users_pending_vote, get_all_users, log_action, \
    get_accepted_outside_bot_requests, get_all_votes_with_names
from config import COMMITTEE_CHAT_ID

router = Router()


def build_keyboard(req, user):
    from bot.db.committee_queries import get_user_role, is_user_admin

    status = req['STATUS']
    ins_id = req['INS_ID']
    role = user['TB_COMMITTEE']
    is_admin = user['IS_ADMIN'] == 1
    # Если user не передан (например, при STATUS = 0)

    # Принять заявку — для секретаря и админа
    if status == 0 and (role == 3 or is_admin):
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Принять заявку", callback_data=f"accept:{ins_id}")]
        ])

    # Одобрить / отклонить — только для председателя и админа
    elif status == 1 and (role == 2 or is_admin):
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve:{ins_id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"decline:{ins_id}")
            ]
        ])

    return None


async def send_new_requests(bot):
    global text
    requests = get_new_requests(status=0)  # Только заявки STATUS = 0
    users = get_all_users()  # Все пользователи для отправки

    for req in requests:
        for user in users:  # ✅ проходим по каждому пользователю
            keyboard = build_keyboard(req, user)
            if keyboard:
                text = (
                    f"📌 Новая заявка | 🆔: {req['INS_ID']}\n"
                    f"👤 Страхователь: {req['OWNER']}\n"
                    f"📅 Период: {req['INS_DATEF']} - {req['INS_DATET']}\n"
                    f"💰 Премия: {req['INS_PREM']} | Отв: {req['INS_OTV']} | Коэф: {req['KEF']}\n"
                    f"📄 Договор: {req['REQ_NAME']}\n"
                    f"📍 Подразделение: {req['DIVISION_ID']}"
                )
                # Найти первого пользователя, у кого есть право принять
        for user in users:
            keyboard = build_keyboard(req, user)
            if keyboard:
                await bot.send_message(chat_id=COMMITTEE_CHAT_ID, text=text, reply_markup=keyboard)
                break  # отправили один раз — достаточно


async def send_followup_requests(bot):

    all_users = get_all_users()

    # 1. Заявки, принятые в АИС
    outside_requests = get_accepted_outside_bot_requests()
    for req in outside_requests:
        votes = get_all_votes_with_names(req['INS_ID'])

        text = (
            f"📌 Заявка | 🆔: {req['INS_ID']} принята на рассмотрение комитетом (из АИС).\n"
            f"👥 Участникам необходимо рассмотреть заявку:\n"
        )
        for user in votes:
            if user["TB_COMMITTEE"] == 1:
                mark = "✅" if user["VOTE"] == 1 else "❌" if user["VOTE"] == 2 else "⏳"
                name = user["FULL_NAME"]
                text += f"{mark} {name}\n"

        candidate = next((u for u in get_all_users() if u['TB_COMMITTEE'] == 2 or u['IS_ADMIN'] == 1), None)
        keyboard = build_keyboard(req, candidate) if candidate else None
        await bot.send_message(chat_id=COMMITTEE_CHAT_ID, text=text, reply_markup=keyboard)

        log_action(
            telegram_id=0,
            action="accept",
            ins_id=req['INS_ID'],
            member_name="Система (АИС)",
            details="Принято в АИС"
        )

    # 2. Остальные заявки со STATUS > 0 И < 2 (т.е. только в процессе)
    requests = [r for r in get_new_requests(status_gt=0) if r['STATUS'] == 1]
    for req in requests:
        votes = get_all_votes_with_names(req['INS_ID'])

        text = (
            f"📌 Заявка | 🆔: {req['INS_ID']} принята на рассмотрение комитетом.\n"
            f"👥 Участникам необходимо рассмотреть заявку:\n"
        )
        for user in votes:
            if user["TB_COMMITTEE"] == 1:
                mark = (
                    "✅" if user['VOTE'] == 1 else
                    "❌" if user['VOTE'] == 2 else
                    "⏳"
                )
                text += f"{mark} {user['FULL_NAME']}\n"

        keyboard = build_keyboard(req, votes[0]) if votes else None
        await bot.send_message(chat_id=COMMITTEE_CHAT_ID, text=text, reply_markup=keyboard)

async def notify_external_acceptances(bot):
    requests = get_accepted_outside_bot_requests()
    for req in requests:
        text = (
            f"📌 Заявка | 🆔: {req['INS_ID']} была принята через АИС.\n"
            f"👤 Страхователь: {req['OWNER']}\n"
            f"📅 Период: {req['INS_DATEF']} - {req['INS_DATET']}\n"
            f"💰 Премия: {req['INS_PREM']} | Отв: {req['INS_OTV']} | Коэф: {req['KEF']}\n"
            f"📄 Договор: {req['REQ_NAME']}\n"
            f"📍 Подразделение: {req['DIVISION_ID']}"
        )
        await bot.send_message(chat_id=COMMITTEE_CHAT_ID, text=text)
        log_action("system", "accept", req['INS_ID'], "АИС", "Принято в АИС")

async def log_external_acceptances():
    requests = get_accepted_outside_bot_requests()
    for req in requests:
        log_action(
            telegram_id=0,
            action="accept",
            ins_id=req['INS_ID'],
            member_name="Система (АИС)",
            details="Принято в АИС"
        )


async def send_final_decisions(bot):
    from bot.db.committee_queries import get_finalized_requests, log_action

    requests = get_finalized_requests()
    for req in requests:
        status = req["STATUS"]
        status_text = "одобрена ✅" if status == 2 else "отклонена ❌"
        text = (
            f"📌 Заявка | 🆔: {req['INS_ID']} {status_text} комитетом."
        )
        await bot.send_message(chat_id=COMMITTEE_CHAT_ID, text=text)

        # Логируем, чтобы не повторно
        log_action(
            telegram_id=0,
            action="final",
            ins_id=req['INS_ID'],
            member_name="Система",
            details=f"Финальный статус: {status_text}"
        )


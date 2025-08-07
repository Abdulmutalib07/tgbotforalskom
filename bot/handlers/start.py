from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot.utils.auth import check_auth

async def cmd_start(message: Message):
    telegram_id = message.from_user.id
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔘 Тест кнопки", callback_data="test:ok")]
    ])
    if await check_auth(telegram_id):
        await message.answer("✅ Добро пожаловать! Вы уже авторизованы.")
    else:
        await message.answer("🔐 Введите логин для авторизации (только логин):")

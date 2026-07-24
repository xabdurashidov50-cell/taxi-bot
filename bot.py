import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# =========================================================
# ⚠️ SHU YERLARGA O'Z MA'LUMOTLARINGIZNI YOZING:
BOT_TOKEN = "8861427129:AAGeUwChMJlME6tuzhjXkptt64kz14vROKE" # BotFather'dan olgan tokeningiz
ADMIN_USERNAME = "TDIU_1"          # Telegram username'ingiz (@ siz)
# =========================================================

# Logging sozlamalari
logging.basicConfig(level=logging.INFO)

# Bot va Dispatcher obyektlari
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- TUGMALAR (KEYBOARDS) ---

# 1. Asosiy menyu (Ekranning pastki qismida turadigan tugmalar)
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🚖 Taksi chaqirish")],
        [KeyboardButton(text="💬 Admin bilan bog'lanish")]
    ],
    resize_keyboard=True
)

# 2. Admin lichkasiga o'tkazuvchi tugma
admin_inline_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="👉 Adminga yozish (Lichka)", url=f"https://t.me/{ADMIN_USERNAME}")]
    ]
)

# --- BUYRUQLAR VA TUGMALAR ISHLOVCHILARI (HANDLERS) ---

# /start buyrug'i kelganda
@dp.message(CommandStart())
async def send_welcome(message: types.Message):
    await message.answer(
        "Xush kelibsiz! Kerakli bo'limni tanlang:",
        reply_markup=main_keyboard
    )

# "💬 Admin bilan bog'lanish" tugmasi bosilganda
@dp.message(F.text == "💬 Admin bilan bog'lanish")
async def contact_admin(message: types.Message):
    await message.answer(
        "Admin bilan bog'lanish uchun pastdagi tugmani bosing:",
        reply_markup=admin_inline_keyboard
    )

# "🚖 Taksi chaqirish" tugmasi bosilganda
@dp.message(F.text == "🚖 Taksi chaqirish")
async def order_taxi(message: types.Message):
    await message.answer("🚖 Taksi chaqirish bo'limi ishga tushdi!")

# --- BOTNI ISHGA TUSHIRISH ---
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())

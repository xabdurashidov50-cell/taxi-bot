import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Bot tokeningizni shu yerga kiritasiz
API_TOKEN = '8861427129:AAGeUwChMJlME6tuzhjXkptt64kz14vROKE'

# Logging sozlamalari
logging.basicConfig(level=logging.INFO)

# Bot va Dispatcher yaratamiz
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# --- TUGMALAR ---
# Asosiy menyu tugmalari
main_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
main_keyboard.add(KeyboardButton("🚖 Taksi chaqirish"))
main_keyboard.add(KeyboardButton("💬 Admin bilan bog'lanish"))

# Admin lichkasiga o'tkazuvchi Inline tugma
# ⚠️ "Sening_Username" o'rniga o'zingizning Telegram username'ingizni yozing!
admin_inline_keyboard = InlineKeyboardMarkup()
admin_inline_keyboard.add(
    InlineKeyboardButton(
        text="👉 Adminga yozish (Lichka)", 
        url="https://t.me/@TDIU_1"
    )
)

# --- HANDLERLAR (BUYRUQLAR) ---

# /start buyrug'i kelganda
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.answer(
        "Xush kelibsiz! Kerakli bo'limni tanlang:",
        reply_markup=main_keyboard
    )

# "💬 Admin bilan bog'lanish" tugmasi bosilganda
@dp.message_handler(text="💬 Admin bilan bog'lanish")
async def contact_admin(message: types.Message):
    await message.answer(
        "Admin bilan bog'lanish uchun pastdagi tugmani bosing:",
        reply_markup=admin_inline_keyboard
    )

# "🚖 Taksi chaqirish" yoki boshqa xabarlar uchun
@dp.message_handler(text="🚖 Taksi chaqirish")
async def order_taxi(message: types.Message):
    await message.answer("Taksi chaqirish bo'limi ishga tushdi!")

# Botni ishga tushirish
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

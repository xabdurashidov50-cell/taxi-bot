import os
import sqlite3
from datetime import datetime, timedelta
import threading
import time
import telebot
from telebot import types

# ⚠️ BOT SOZLAMALARI
TOKEN = "8861427129:AAGeUwChMJlME6tuzhjXkptt64kz14vROKE"
MAIN_ADMIN = 5298898042  # Asosiy Admin Telegram ID'si
TARGET_GROUP = -1004346220056  # Asosiy guruh ID'si

# 💳 KARTA VA TO'LOV SOZLAMALARI (30 KUN / 30 000 SO'M)
CARD_NUMBER = "9860 1666 5687 3972"
CARD_OWNER = "Raxmonov O"
SUBSCRIPTION_PRICE = "30 000"

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# 🔘 BOT BUYRUQLAR MENYUSI
try:
    bot.set_my_commands([
        types.BotCommand("start", "Botni qayta ishga tushirish")
    ])
except Exception as e:
    print(f"Buyruqlarni sozlashda xato: {e}")

# --- DATABASE (MA'LUMOTLAR BAZASI) ---

def init_db():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS drivers (
            user_id INTEGER PRIMARY KEY,
            phone TEXT,
            sub_end_date DATETIME,
            status TEXT,
            warning_date DATETIME
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS channels (
            channel_id INTEGER PRIMARY KEY,
            title TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY
        )
    ''')

    cursor.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (MAIN_ADMIN,))
    
    conn.commit()
    conn.close()

init_db()

user_data = {}
orders_db = []

def get_admins():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM admins")
    admins = [row[0] for row in cursor.fetchall()]
    conn.close()
    return admins

# --- MENYULAR ---

def bosh_menyu(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton(text="🚖 Taxi buyurtma")
    btn2 = types.KeyboardButton(text="🚖 Taksislar uchun")
    btn3 = types.KeyboardButton(text="📋 Buyurtmalarim")
    markup.row(btn1, btn2)
    markup.row(btn3)
    
    if user_id in get_admins():
        btn_admin = types.KeyboardButton(text="🗄 Boshqaruv")
        markup.row(btn_admin)
        
    return markup

def admin_menyu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton(text="📊 Statistika")
    btn2 = types.KeyboardButton(text="📢 Kanallar / Guruhlar")
    btn3 = types.KeyboardButton(text="👥 Admin qo'shish")
    btn4 = types.KeyboardButton(text="📋 Barcha buyurtmalar")
    btn5 = types.KeyboardButton(text="🏠 Bosh menyu")
    markup.row(btn1, btn2)
    markup.row(btn3, btn4)
    markup.row(btn5)
    return markup

def ha_yoq_menyusi():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("✅ Ha"), types.KeyboardButton("❌ Yo'q"))
    return markup

def pay_cancel_menyusi():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("💳 To'lov qilish"), types.KeyboardButton("❌ Rad etish"))
    return markup

def bekor_qilish_menyusi():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("❌ Bekor qilish"))
    return markup

def tur_menyusi():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("🚖 Taxi"), types.KeyboardButton("📦 Pochta"))
    markup.row(types.KeyboardButton("❌ Bekor qilish"))
    return markup

def odam_soni_menyusi():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(
        types.KeyboardButton("1"), types.KeyboardButton("2"),
        types.KeyboardButton("3"), types.KeyboardButton("4")
    )
    markup.row(types.KeyboardButton("❌ Bekor qilish"))
    return markup

# --- HANDLERLAR ---

@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

    if message.chat.id in user_data:
        del user_data[message.chat.id]
    bot.send_message(message.chat.id, "👋 Assalomu alaykum!\n\n🚖 Taxi va Pochta xizmati botiga xush kelibsiz.", reply_markup=bosh_menyu(user_id))

@bot.message_handler(func=lambda msg: msg.text == "❌ Bekor qilish")
def cancel_action(message):
    chat_id = message.chat.id
    if chat_id in user_data:
        del user_data[chat_id]
    bot.send_message(chat_id, "❌ Amal bekor qilindi.", reply_markup=bosh_menyu(message.from_user.id))

@bot.message_handler(func=lambda msg: msg.text == "🏠 Bosh menyu")
def back_to_main(message):
    bot.send_message(message.chat.id, "🏠 Bosh menyuga qaytdingiz.", reply_markup=bosh_menyu(message.from_user.id))

# --- ADMIN PANEL ---

@bot.message_handler(func=lambda msg: msg.text == "🗄 Boshqaruv")
def admin_panel(message):
    if message.from_user.id in get_admins():
        bot.send_message(message.chat.id, "🗄 <b>Admin paneliga xush kelibsiz!</b>\n\nKerakli bo'limni tanlang:", reply_markup=admin_menyu())

@bot.message_handler(func=lambda msg: msg.text == "📊 Statistika")
def show_stats(message):
    if message.from_user.id in get_admins():
        conn = sqlite3.connect("bot_database.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM drivers WHERE status = 'active'")
        active_drivers = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM admins")
        total_admins = cursor.fetchone()[0]
        
        conn.close()
        
        text = (
            f"📊 <b>BOT STATISTIKASI:</b>\n\n"
            f"👤 <b>Jami foydalanuvchilar:</b> {total_users} ta\n"
            f"🚖 <b>Faol taksichilar:</b> {active_drivers} ta\n"
            f"📦 <b>Jami buyurtmalar:</b> {len(orders_db)} ta\n"
            f"👥 <b>Adminlar soni:</b> {total_admins} ta"
        )
        bot.send_message(message.chat.id, text, reply_markup=admin_menyu())

@bot.message_handler(func=lambda msg: msg.text == "👥 Admin qo'shish")
def add_admin_start(message):
    if message.from_user.id in get_admins():
        msg = bot.send_message(message.chat.id, "👤 Yangi adminning <b>Telegram ID</b> raqamini kiriting:", reply_markup=bekor_qilish_menyusi())
        bot.register_next_step_handler(msg, process_add_admin)

def process_add_admin(message):
    if message.text == "❌ Bekor qilish":
        cancel_action(message); return
        
    try:
        new_admin_id = int(message.text)
        conn = sqlite3.connect("bot_database.db")
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (new_admin_id,))
        conn.commit()
        conn.close()
        
        bot.send_message(message.chat.id, f"✅ ID: <code>{new_admin_id}</code> muvaffaqiyatli admin qilindi!", reply_markup=admin_menyu())
    except ValueError:
        bot.send_message(message.chat.id, "⚠️ Iltimos, faqat raqamlardan iborat Telegram ID kiriting!", reply_markup=admin_menyu())

@bot.message_handler(func=lambda msg: msg.text == "📢 Kanallar / Guruhlar")
def manage_channels(message):
    if message.from_user.id in get_admins():
        conn = sqlite3.connect("bot_database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT channel_id, title FROM channels")
        channels = cursor.fetchall()
        conn.close()
        
        markup = types.InlineKeyboardMarkup()
        for ch_id, title in channels:
            markup.add(types.InlineKeyboardButton(text=f"❌ {title}", callback_data=f"delchan_{ch_id}"))
            
        markup.add(types.InlineKeyboardButton(text="➕ Yangi guruh/kanal qo'shish", callback_data="add_channel"))
        
        bot.send_message(
            message.chat.id, 
            "📢 <b>Ulangan guruhlar va kanallar:</b>\n\nO'chirish uchun kanal ustiga bosing yoki yangisini qo'shing:", 
            reply_markup=markup
        )

@bot.callback_query_handler(func=lambda call: call.data == "add_channel" or call.data.startswith("delchan_"))
def channel_callback(call):
    if call.data == "add_channel":
        msg = bot.send_message(
            call.message.chat.id, 
            "➕ Botni o'sha guruh/kanalga <b>ADMIN</b> qiling va uning <b>ID raqamini</b> yuboring (Masalan: <code>-100123456789</code>):"
        )
        bot.register_next_step_handler(msg, process_add_channel)
    elif call.data.startswith("delchan_"):
        ch_id = int(call.data.split("_")[1])
        conn = sqlite3.connect("bot_database.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM channels WHERE channel_id = ?", (ch_id,))
        conn.commit()
        conn.close()
        bot.answer_callback_query(call.id, "O'chirildi!")
        bot.send_message(call.message.chat.id, "✅ Guruh/Kanal ro'yxatdan o'chirildi.", reply_markup=admin_menyu())

def process_add_channel(message):
    try:
        ch_id = int(message.text)
        chat = bot.get_chat(ch_id)
        
        conn = sqlite3.connect("bot_database.db")
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO channels (channel_id, title) VALUES (?, ?)", (ch_id, chat.title))
        conn.commit()
        conn.close()
        
        bot.send_message(message.chat.id, f"✅ <b>{chat.title}</b> muvaffaqiyatli bazaga qo'shildi!", reply_markup=admin_menyu())
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Xatolik! Bot guruhda admin ekanligini va ID to'g'riligini tekshiring.\nXato: {e}", reply_markup=admin_menyu())

@bot.message_handler(func=lambda msg: msg.text == "📋 Barcha buyurtmalar")
def show_all_orders(message):
    if message.from_user.id in get_admins():
        if not orders_db:
            bot.send_message(message.chat.id, "📋 Hozircha hech qanday buyurtma tushgani yo'q.", reply_markup=admin_menyu())
        else:
            text = "📋 <b>Oxirgi buyurtmalar ro'yxati:</b>\n\n"
            for idx, o in enumerate(orders_db[-10:], 1):
                text += f"{idx}. {o.get('tur')} | {o.get('qayerdan')} ➡️ {o.get('qayerga')} | Tel: {o.get('phone')}\n"
            bot.send_message(message.chat.id, text, reply_markup=admin_menyu())

# --- BUYURTMA BERISH BO'LIMI ---

@bot.message_handler(func=lambda msg: msg.text == "🚖 Taxi buyurtma")
def order_start(message):
    chat_id = message.chat.id
    user_data[chat_id] = {'user_id': message.from_user.id}
    bot.send_message(chat_id, "🚖 Buyurtma turini tanlang:", reply_markup=tur_menyusi())

@bot.message_handler(func=lambda msg: msg.text in ["🚖 Taxi", "📦 Pochta"])
def select_type(message):
    chat_id = message.chat.id
    if chat_id not in user_data:
        user_data[chat_id] = {'user_id': message.from_user.id}
        
    user_data[chat_id]['tur'] = message.text
    
    if message.text == "🚖 Taxi":
        msg = bot.send_message(chat_id, "👥 Nechta yo'lovchi?", reply_markup=odam_soni_menyusi())
        bot.register_next_step_handler(msg, get_passengers)
    else:
        user_data[chat_id]['soni'] = "Pochta"
        msg = bot.send_message(chat_id, "📍 Qayerdan ketasiz?\n\nMasalan: Toshkent, Chilonzor", reply_markup=bekor_qilish_menyusi())
        bot.register_next_step_handler(msg, get_location)

def get_passengers(message):
    chat_id = message.chat.id
    if message.text == "❌ Bekor qilish":
        cancel_action(message); return
        
    user_data[chat_id]['soni'] = message.text
    msg = bot.send_message(chat_id, "📍 Qayerdan ketasiz?\n\nMasalan: Toshkent, Chilonzor", reply_markup=bekor_qilish_menyusi())
    bot.register_next_step_handler(msg, get_location)

def get_location(message):
    chat_id = message.chat.id
    if message.text == "❌ Bekor qilish":
        cancel_action(message); return
        
    user_data[chat_id]['qayerdan'] = message.text
    msg = bot.send_message(chat_id, "🏁 Qayerga borasiz?\n\nMasalan: Samarqand, Markaz", reply_markup=bekor_qilish_menyusi())
    bot.register_next_step_handler(msg, get_destination)

def get_destination(message):
    chat_id = message.chat.id
    if message.text == "❌ Bekor qilish":
        cancel_action(message); return
        
    user_data[chat_id]['qayerga'] = message.text
    msg = bot.send_message(chat_id, "📞 Telefon raqamingizni kiriting:\n\nMasalan: +998901234567", reply_markup=bekor_qilish_menyusi())
    bot.register_next_step_handler(msg, finish_order)

def finish_order(message):
    chat_id = message.chat.id
    if message.text == "❌ Bekor qilish":
        cancel_action(message); return
        
    user_data[chat_id]['phone'] = message.text
    orders_db.append(user_data[chat_id])
    
    tur = user_data[chat_id].get('tur', '-')
    soni = user_data[chat_id].get('soni', '-')
    qayerdan = user_data[chat_id].get('qayerdan', '-')
    qayerga = user_data[chat_id].get('qayerga', '-')
    phone = user_data[chat_id].get('phone', '-')
    user_link = f"@{message.from_user.username}" if message.from_user.username else "Mavjud emas"
    
    order_post = (
        f"🆕 <b>YANGI BUYURTMA!</b>\n\n"
        f"📌 <b>Turi:</b> {tur}\n"
    )
    if tur == "🚖 Taxi":
        order_post += f"👥 <b>Odam soni:</b> {soni} kishi\n"
        
    order_post += (
        f"📍 <b>Qayerdan:</b> {qayerdan}\n"
        f"🏁 <b>Qayerga:</b> {qayerga}\n"
        f"📞 <b>Tel:</b> {phone}\n"
        f"👤 <b>Mijoz:</b> {user_link}"
    )
    
    try:
        bot.send_message(TARGET_GROUP, order_post)
    except Exception as e:
        print(f"Guruhga yuborishda xatolik: {e}")
        
    bot.send_message(chat_id, "✅ Buyurtmangiz qabul qilindi va guruhga joylandi!", reply_markup=bosh_menyu(message.from_user.id))
    
    if chat_id in user_data:
        del user_data[chat_id]

# --- TAKSISLAR UCHUN VA TO'LOV BO'LIMI ---

@bot.message_handler(func=lambda msg: msg.text == "🚖 Taksislar uchun")
def driver_start(message):
    chat_id = message.chat.id
    user_data[chat_id] = {'role': 'driver'}
    msg = bot.send_message(
        chat_id, 
        "📞 Telefon raqamingizni yozing (Masalan: +998901234567):", 
        reply_markup=bekor_qilish_menyusi()
    )
    bot.register_next_step_handler(msg, process_driver_phone)

def process_driver_phone(message):
    chat_id = message.chat.id
    if message.text == "❌ Bekor qilish":
        cancel_action(message); return

    user_data[chat_id]['phone'] = message.text

    msg = bot.send_message(
        chat_id, 
        "🚖 Taksi guruhimizga qo'shilasizmi?", 
        reply_markup=ha_yoq_menyusi()
    )
    bot.register_next_step_handler(msg, process_driver_join)

def process_driver_join(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    if message.text == "✅ Ha":
        send_payment_info(chat_id)
    else:
        bot.send_message(chat_id, "🏠 Bosh menyuga qaytdingiz.", reply_markup=bosh_menyu(user_id))

def send_payment_info(chat_id):
    text = (
        f"💳 <b>Guruhga qo'shilish uchun to'lov ma'lumotlari:</b>\n\n"
        f"💰 <b>To'lov summasi:</b> {SUBSCRIPTION_PRICE} so'm\n"
        f"💳 <b>Karta raqam:</b> <code>{CARD_NUMBER}</code>\n"
        f"👤 <b>Ega:</b> {CARD_OWNER}\n\n"
        f"📸 To'lovni amalga oshirgach, <b>to'lov chekining rasm (skrinshot)ini</b> shu yerga yuboring:"
    )
    msg = bot.send_message(chat_id, text, reply_markup=bekor_qilish_menyusi())
    bot.register_next_step_handler(msg, process_check_photo)

def process_check_photo(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    if message.text == "❌ Bekor qilish":
        cancel_action(message); return

    if not message.photo:
        msg = bot.send_message(chat_id, "⚠️ Iltimos, faqat to'lov chekining **rasmini** yuboring!")
        bot.register_next_step_handler(msg, process_check_photo)
        return

    photo_id = message.photo[-1].file_id
    phone = user_data.get(chat_id, {}).get('phone', 'Kiritilmagan')

    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve_{user_id}"),
        types.InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_{user_id}")
    )

    caption = (
        f"📥 <b>YANGI TO'LOV CHEKI! ({SUBSCRIPTION_PRICE} So'm)</b>\n\n"
        f"👤 <b>Foydalanuvchi:</b> <a href='tg://user?id={user_id}'>{message.from_user.first_name}</a>\n"
        f"📞 <b>Tel:</b> {phone}\n"
        f"🆔 <b>ID:</b> <code>{user_id}</code>"
    )

    for admin_id in get_admins():
        try:
            bot.send_photo(admin_id, photo_id, caption=caption, reply_markup=markup)
        except Exception:
            pass

    bot.send_message(chat_id, "⏳ Chekingiz adminga yuborildi. Tasdiqlanishini kuting...", reply_markup=bosh_menyu(user_id))

# --- ADMIN TASDIQLASHI VA CALLBACK HANDLER ---

@bot.callback_query_handler(func=lambda call: call.data.startswith(("approve_", "reject_")))
def admin_check_callback(call):
    if call.from_user.id not in get_admins():
        bot.answer_callback_query(call.id, "Ruxsat berilmagan!")
        return

    data = call.data.split("_")
    action = data[0]
    target_user_id = int(data[1])

    if action == "approve":
        try:
            invite_link = bot.create_chat_invite_link(chat_id=TARGET_GROUP, member_limit=1)
            phone = user_data.get(target_user_id, {}).get('phone', 'Kiritilmagan')
            sub_end = datetime.now() + timedelta(days=30)
            
            conn = sqlite3.connect("bot_database.db")
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO drivers (user_id, phone, sub_end_date, status, warning_date)
                VALUES (?, ?, ?, 'active', NULL)
            ''', (target_user_id, phone, sub_end))
            conn.commit()
            conn.close()

            text = (
                f"🎉 <b>To'lov tasdiqlandi!</b>\n\n"
                f"📅 Obunangiz 30 kun davomida faol.\n"
                f"🔗 Maxfiy guruh havolasi:\n{invite_link.invite_link}\n\n"
                f"⚠️ <i>Havolaga faqat 1 kishi kirishi mumkin!</i>"
            )
            bot.send_message(target_user_id, text, reply_markup=bosh_menyu(target_user_id))
            bot.edit_message_caption(f"{call.message.caption}\n\n✅ <b>TASDIQLANDI (30 KUN)</b>", call.message.chat.id, call.message.message_id)
            bot.answer_callback_query(call.id, "Tasdiqlandi!")

        except Exception as e:
            bot.send_message(call.message.chat.id, f"⚠️ **Tasdiqlashda xatolik:**\n\n<code>{e}</code>")
            bot.answer_callback_query(call.id, "Xatolik yuz berdi!", show_alert=True)

    elif action == "reject":
        try:
            bot.send_message(target_user_id, "❌ Kechirasiz, to'lovingiz admin tomonidan rad etildi.")
            bot.edit_message_caption(f"{call.message.caption}\n\n❌ <b>RAD ETILDI</b>", call.message.chat.id, call.message.message_id)
            bot.answer_callback_query(call.id, "Rad etildi!")
        except Exception as e:
            bot.send_message(call.message.chat.id, f"⚠️ Rad etishda xato: {e}")

# --- QAYTA TO'LOV QILISH YOKI RAD ETISH ---

@bot.message_handler(func=lambda msg: msg.text in ["💳 To'lov qilish", "❌ Rad etish"])
def renewal_choice(message):
    user_id = message.from_user.id
    if message.text == "💳 To'lov qilish":
        send_payment_info(message.chat.id)
    elif message.text == "❌ Rad etish":
        try:
            bot.ban_chat_member(TARGET_GROUP, user_id)
            bot.unban_chat_member(TARGET_GROUP, user_id)
            
            conn = sqlite3.connect("bot_database.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM drivers WHERE user_id = ?", (user_id,))
            conn.commit()
            conn.close()

            bot.send_message(message.chat.id, "❌ Obunani rad etdingiz. Guruhdan chiqarildingiz.", reply_markup=bosh_menyu(user_id))
        except Exception:
            bot.send_message(message.chat.id, "🏠 Bosh menyuga qaytdingiz.", reply_markup=bosh_menyu(user_id))

# --- BUYURTMALARIM BO'LIMI ---

@bot.message_handler(func=lambda msg: msg.text == "📋 Buyurtmalarim")
def my_orders(message):
    user_orders = [o for o in orders_db if o.get('user_id') == message.from_user.id]
    if not user_orders:
        bot.send_message(message.chat.id, "📋 Sizda hali faol buyurtmalar yo'q.", reply_markup=bosh_menyu(message.from_user.id))
    else:
        res = ""
        for idx, o in enumerate(user_orders, 1):
            res += f"{idx}. {o.get('tur')} | {o.get('qayerdan')} ➡️ {o.get('qayerga')}\n"
        bot.send_message(message.chat.id, f"📋 <b>Sizning buyurtmalaringiz:</b>\n\n{res}", reply_markup=bosh_menyu(message.from_user.id))

# --- AVTO-TEKSHIRUV BO'LIMI ---

def auto_check_subscriptions():
    while True:
        try:
            conn = sqlite3.connect("bot_database.db")
            cursor = conn.cursor()
            now = datetime.now()

            cursor.execute("SELECT user_id, sub_end_date FROM drivers WHERE status = 'active'")
            active_drivers = cursor.fetchall()

            for user_id, sub_end_str in active_drivers:
                sub_end = datetime.strptime(sub_end_str.split(".")[0], "%Y-%m-%d %H:%M:%S")
                
                if now >= sub_end:
                    cursor.execute(
                        "UPDATE drivers SET status = 'warning', warning_date = ? WHERE user_id = ?",
                        (now, user_id)
                    )
                    conn.commit()
                    
                    warning_text = (
                        "⏰ <b>OBUNA MUDDATINGIZ TUGADI!</b>\n\n"
                        f"Taksi guruhidan foydalanishni davom ettirish uchun {SUBSCRIPTION_PRICE} so'm to'lovni amalga oshiring.\n\n"
                        "⚠️ <b>Agar 24 soat ichida to'lov qilmasangiz, guruhdan avtomatik tarzda chiqarib yuborilasiz!</b>"
                    )
                    try:
                        bot.send_message(user_id, warning_text, reply_markup=pay_cancel_menyusi())
                    except Exception as e:
                        print(f"Xabar yuborishda xato: {e}")

            cursor.execute("SELECT user_id, warning_date FROM drivers WHERE status = 'warning'")
            warning_drivers = cursor.fetchall()

            for user_id, warn_date_str in warning_drivers:
                if warn_date_str:
                    warn_date = datetime.strptime(warn_date_str.split(".")[0], "%Y-%m-%d %H:%M:%S")
                    
                    if now >= (warn_date + timedelta(hours=24)):
                        try:
                            bot.ban_chat_member(TARGET_GROUP, user_id)
                            bot.unban_chat_member(TARGET_GROUP, user_id)
                            
                            cursor.execute("DELETE FROM drivers WHERE user_id = ?", (user_id,))
                            conn.commit()

                            kick_text = "❌ 24 soat ichida to'lov qilinmagani sababli taksi guruhidan chiqarib yuborildingiz."
                            bot.send_message(user_id, kick_text, reply_markup=bosh_menyu(user_id))
                        except Exception as e:
                            print(f"Guruhdan chiqarishda xato: {e}")

            conn.close()
        except Exception as e:
            print(f"Obuna avto-tekshiruvida xatolik: {e}")

        time.sleep(1800)

threading.Thread(target=auto_check_subscriptions, daemon=True).start()

print("Bot muvaffaqiyatli ishga tushdi...")
bot.infinity_polling()

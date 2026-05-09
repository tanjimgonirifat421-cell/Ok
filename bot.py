import random
import string
import time
import hashlib
import hmac
import base64
import struct
import telebot
from telebot import types
import sqlite3
from datetime import datetime
from flask import Flask
from threading import Thread

# ================= CONFIGURATION =================
TOKEN = "8783194900:AAH__MsqIgqwKn_-Pzg2NdxQsIJ1OjvAVY8"
ADMIN_ID = 8783194900 
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
app = Flask('')

# ================= DATABASE INIT =================
def init_db():
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, 
        username TEXT, 
        balance REAL DEFAULT 0,
        invites INTEGER DEFAULT 0, 
        referrer_id INTEGER, 
        last_task_time REAL DEFAULT 0
    )""")
    conn.commit()
    conn.close()

init_db()

# ================= CORE LOGIC HELPERS =================

# ৭ অক্ষরের নাম + আজকের তারিখ (যেমন: Tanjimz09)
def generate_smart_pass():
    names = ["Tanjimz", "Saidurz", "Rifatxx", "Mimproo", "Siyamzz"]
    selected_name = random.choice(names)
    day = datetime.now().strftime("%d")
    return f"{selected_name}{day}"

# ২এফএ ওটিপি জেনারেটর
def get_totp_code(secret):
    try:
        clean_sec = ''.join(c for c in secret if c.isalnum()).upper()
        key = base64.b32decode(clean_sec + '=' * ((8 - len(clean_sec) % 8) % 8))
        counter = struct.pack('>Q', int(time.time() // 30))
        hmac_hash = hmac.new(key, counter, hashlib.sha1).digest()
        offset = hmac_hash[-1] & 0x0F
        code = (struct.unpack('>I', hmac_hash[offset:offset+4])[0] & 0x7FFFFFFF) % 1000000
        return f"{code:06d}"
    except:
        return "Invalid Key"

# ================= KEYBOARDS =================

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("📋 Tasks", "💰 Balance", "📤 Withdraw", "👤 Profile")
    markup.add("🏆 Top Users", "👥 Referrals", "🌍 Language")
    return markup

def task_category_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("📸 Instagram", "📘 Facebook", "❌ Cancel")
    return markup

# ================= BOT HANDLERS =================

@bot.message_handler(commands=['start'])
def welcome(message):
    uid = message.from_user.id
    uname = message.from_user.first_name
    
    # রেফারেল সিস্টেম (লিঙ্ক থেকে আসলে)
    ref_id = None
    if len(message.text.split()) > 1 and "ref_" in message.text:
        try:
            ref_id = int(message.text.split()[1].split('_')[1])
            if ref_id == uid: ref_id = None
        except: ref_id = None

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO users (user_id, username, referrer_id) VALUES (?,?,?)", (uid, uname, ref_id))
    conn.commit()
    conn.close()
    
    bot.send_message(message.chat.id, f"👋 Welcome to Task Bot, <b>{uname}</b>!", reply_markup=main_menu())

# --- 📋 Tasks Flow ---
@bot.message_handler(func=lambda m: m.text == "📋 Tasks")
def tasks_menu(message):
    bot.send_message(message.chat.id, "👇 Please select a task category:", reply_markup=task_category_menu())

# --- 📸 Instagram Flow ---
@bot.message_handler(func=lambda m: m.text == "📸 Instagram")
def ig_info(message):
    text = """
⏳ Review time: 64 minutes
📋 <b>Instagram Account Setup</b>
📄 You need to create a new Instagram account.
🔐 <b>Important:</b>
• Use only the given information
• Complete all steps correctly
"""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("▶️ Start", callback_data="start_ig"))
    markup.add(types.InlineKeyboardButton("❌ Cancel", callback_data="cancel_task"))
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "start_ig")
def start_ig_logic(call):
    uid = call.from_user.id
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("SELECT last_task_time FROM users WHERE user_id=?", (uid,))
    last_time = cur.fetchone()[0]
    conn.close()

    # ৩ মিনিটের সিকিউরিটি ব্লক
    if time.time() - last_time < 180:
        bot.answer_callback_query(call.id, "⚠️ Security block! Wait 3 minutes.", show_alert=True)
        return

    psw = generate_smart_pass()
    bot.send_message(call.message.chat.id, "⏳ Ordering email, please wait...")
    time.sleep(1.5)
    
    task_details = f"""
First name: Santo Domingo
Login: ig_user_{random.randint(1000,9999)}
Password: <code>{psw}</code>
Email: (Fetching from system...)
"""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📥 Get Code", callback_data="get_ig_code"))
    bot.send_message(call.message.chat.id, task_details, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "get_ig_code")
def get_code_prompt(call):
    msg = bot.send_message(call.message.chat.id, "🔑 Please enter your <b>2FA Secret Key</b> to get the code:")
    bot.register_next_step_handler(msg, process_2fa_and_code)

def process_2fa_and_code(message):
    secret = message.text.strip()
    otp = get_totp_code(secret)
    
    # লাস্ট টাস্ক টাইম আপডেট (৩ মিনিট ব্লকের জন্য)
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("UPDATE users SET last_task_time = ? WHERE user_id = ?", (time.time(), message.from_user.id))
    conn.commit()
    conn.close()

    resp = f"1otp\n2SMS 📋 Your one-time code:\n\n<code>{otp}</code>\n\n👆 Tap the code to copy\n3SmS 👉 Press the button to confirm registration:"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Account registered", callback_data="final_report"))
    bot.send_message(message.chat.id, resp, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "final_report")
def final_report(call):
    bot.edit_message_text("✅ Your report has been received! Please wait.", call.message.chat.id, call.message.message_id)

# --- 👑 Admin Panel ---
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("✅ Approve Bulk", "📊 Stats")
        bot.send_message(message.chat.id, "👑 Admin Panel Activated", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "✅ Approve Bulk" and m.from_user.id == ADMIN_ID)
def approve_bulk(message):
    msg = bot.send_message(message.chat.id, "Paste Username List (One per line):")
    bot.register_next_step_handler(msg, process_bulk)

def process_bulk(message):
    names = message.text.split('\n')
    for n in names:
        if n.strip():
            bot.send_message(message.chat.id, f"✅ Approved: <code>{n.strip()}</code>")
    bot.send_message(message.chat.id, "🏁 All processed successfully!")

# ================= WEB SERVER (KEEP ALIVE) =================
@app.route('/')
def home(): return "Bot is Alive"
def run_web(): app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    t = Thread(target=run_web)
    t.start()
    print("Bot is polling...")
    bot.infinity_polling()
  

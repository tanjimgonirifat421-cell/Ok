import telebot
import random
import string
import time
import sqlite3
import requests
import base64
import hmac
import hashlib
import struct
import logging
from telebot import types
from datetime import datetime
from flask import Flask
from threading import Thread

# ================= CONFIGURATION =================
TOKEN = "8783194900:AAH__MsqIgqwKn_-Pzg2NdxQsIJ1OjvAVY8"
ADMIN_ID = 8783194900 
CHANNEL_LINK = "https://t.me/ws_vip_season_"
SUPPORT_USER = "@FB_SALL_AD"

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
app = Flask('')

# Logging setup for debugging
logging.basicConfig(level=logging.INFO)

# ================= DATABASE LAYER =================
def init_db():
    conn = sqlite3.connect("master_data.db")
    cur = conn.cursor()
    # Users table
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, 
        username TEXT, 
        balance REAL DEFAULT 0,
        invites INTEGER DEFAULT 0,
        referrer_id INTEGER,
        last_task_time REAL DEFAULT 0,
        lang TEXT DEFAULT 'BN'
    )""")
    # Task Reports table
    cur.execute("""CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        task_type TEXT,
        data TEXT,
        status TEXT DEFAULT 'Pending',
        timestamp TEXT
    )""")
    conn.commit()
    conn.close()

init_db()

# ================= SMART HELPERS =================

def get_smart_pass():
    """আপনার সেই ৭ অক্ষরের নাম + আজকের তারিখ লজিক"""
    names = ["Tanjimz", "Saidurz", "Rifatxx", "Mimproo", "Siyamzz", "Cyberxx"]
    name = random.choice(names)
    day = datetime.now().strftime("%d")
    return f"{name}{day}"

def get_2fa_otp(secret):
    """২এফএ সিক্রেট থেকে ৬ ডিজিটের কোড বের করার লজিক"""
    try:
        secret = secret.replace(" ", "").upper()
        key = base64.b32decode(secret + '=' * ((8 - len(secret) % 8) % 8))
        counter = struct.pack('>Q', int(time.time() // 30))
        hmac_hash = hmac.new(key, counter, hashlib.sha1).digest()
        offset = hmac_hash[-1] & 0x0F
        code = (struct.unpack('>I', hmac_hash[offset:offset+4])[0] & 0x7FFFFFFF) % 1000000
        return f"{code:06d}"
    except Exception as e:
        return f"Error: {str(e)}"

# ================= KEYBOARDS (Full Menu) =================

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("📋 Tasks", "💰 Balance")
    markup.add("📤 Withdraw", "👤 Profile")
    markup.add("🏆 Top Users", "👥 Referrals")
    markup.add("🌍 Language", "📞 Support")
    return markup

def task_categories():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("📸 Instagram 2FA", "🍪 IG Cookies")
    markup.add("📘 Facebook Task", "❌ Cancel")
    return markup

# ================= CORE HANDLERS =================

@bot.message_handler(commands=['start'])
def welcome(message):
    uid = message.from_user.id
    uname = message.from_user.first_name
    
    # Referral Tracking logic
    ref_id = None
    if "ref_" in message.text:
        try:
            ref_id = int(message.text.split()[1].split('_')[1])
            if ref_id == uid: ref_id = None
        except: ref_id = None

    conn = sqlite3.connect("master_data.db")
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO users (user_id, username, referrer_id) VALUES (?,?,?)", (uid, uname, ref_id))
    conn.commit()
    conn.close()

    welcome_text = f"━━━━━━━━━━━━━━━━━━━━━━\n👋 Welcome to Task Bot, <b>{uname}</b>!\n━━━━━━━━━━━━━━━━━━━━━━"
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "❌ Cancel")
def back_home(message):
    bot.send_message(message.chat.id, "🏠 ফিরে আসা হয়েছে মেইন মেনুতে।", reply_markup=main_menu())

# --- 📋 TASK SYSTEM (STEP-BY-STEP) ---

@bot.message_handler(func=lambda m: m.text == "📋 Tasks")
def show_tasks(message):
    bot.send_message(message.chat.id, "👇 Please select a task category:", reply_markup=task_categories())

@bot.message_handler(func=lambda m: m.text == "📸 Instagram 2FA")
def ig_task_init(message):
    # ইনস্ট্রাকশন ফ্লো
    instr = """
⏳ Review time: 64 minutes
📋 <b>Instagram Account Setup</b>
📄 নতুন ইন্সটাগ্রাম অ্যাকাউন্ট তৈরি করুন।
🔐 <b>Important:</b>
• নিচে দেওয়া পাসওয়ার্ড ব্যবহার করুন।
• ওটিপি এর জন্য নিচের বাটন চাপুন।
"""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("▶️ Start Task", callback_data="start_ig_2fa"))
    bot.send_message(message.chat.id, instr, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "start_ig_2fa")
def ig_start_logic(call):
    uid = call.from_user.id
    conn = sqlite3.connect("master_data.db")
    cur = conn.cursor()
    cur.execute("SELECT last_task_time FROM users WHERE user_id=?", (uid,))
    last_time = cur.fetchone()[0]
    conn.close()

    # ৩ মিনিটের সিকিউরিটি লক
    if time.time() - last_time < 180:
        bot.answer_callback_query(call.id, "⚠️ Security block! ৩ মিনিট অপেক্ষা করুন।", show_alert=True)
        return

    psw = get_smart_pass()
    # Tmailor.com লজিক (র্যান্ডম মেইল জেনারেশন সিমুলেশন)
    temp_email = f"tan_{random.randint(1000,9999)}@tmailor.com"
    
    bot.send_message(call.message.chat.id, "⏳ Ordering email, please wait...")
    time.sleep(1)
    
    task_msg = f"""
1️⃣ <b>Like Task Selected</b>
━━━━━━━━━━━━━━━━━━━━━━
📧 Email: <code>{temp_email}</code>
🔑 Password: <code>{psw}</code>
━━━━━━━━━━━━━━━━━━━━━━
👇 মেইলে কোড পাঠিয়ে নিচের বাটনে চাপ দিন।
"""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📥 Get Mail OTP", callback_data="fetch_mail_otp"))
    bot.send_message(call.message.chat.id, task_msg, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "fetch_mail_otp")
def fetch_otp(call):
    # এখানে আপনার API এর মাধ্যমে ইনবক্স চেক করার লজিক বসবে
    bot.send_message(call.message.chat.id, "2SMS 🔍 Searching for email, please wait...")
    time.sleep(2)
    sample_otp = random.randint(111111, 999999)
    
    resp = f"3SMS 📋 Code from email:\n\n<code>{sample_otp}</code>\n\n👆 Tap to copy.\n\n4SMS 🔑 এখন আপনার <b>2FA Secret Key</b> টি পাঠান:"
    bot.send_message(call.message.chat.id, resp)
    bot.register_next_step_handler(call.message, process_2fa_final)

def process_2fa_final(message):
    secret = message.text.strip()
    two_fa_otp = get_2fa_otp(secret)
    
    # লাস্ট টাস্ক টাইম আপডেট
    conn = sqlite3.connect("master_data.db")
    cur = conn.cursor()
    cur.execute("UPDATE users SET last_task_time = ? WHERE user_id = ?", (time.time(), message.from_user.id))
    conn.commit()
    conn.close()

    final_text = f"1otp\n2SMS 📋 Your 2FA code:\n\n<code>{two_fa_otp}</code>\n\n👆 Tap to copy.\n\n3SmS 👉 কাজ শেষ হলে নিচের বাটনে রিপোর্ট দিন।"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Account Registered", callback_data="task_complete_final"))
    bot.send_message(message.chat.id, final_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "task_complete_final")
def task_done(call):
    bot.edit_message_text("✅ Your report has been received! Please wait.", call.message.chat.id, call.message.message_id)

# --- 🍪 COOKIES TASK ---

@bot.message_handler(func=lambda m: m.text == "🍪 IG Cookies")
def ig_cookies_task(message):
    msg = bot.send_message(message.chat.id, "📄 আপনার ইন্সটাগ্রাম কুকি (JSON/Netscape) এখানে পেস্ট করুন:")
    bot.register_next_step_handler(msg, save_cookie_report)

def save_cookie_report(message):
    cookie_data = message.text
    # ডাটাবেজে সেভ
    conn = sqlite3.connect("master_data.db")
    cur = conn.cursor()
    cur.execute("INSERT INTO reports (user_id, task_type, data, timestamp) VALUES (?,?,?,?)", 
                (message.from_user.id, "Cookies", cookie_data, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ কুকি রিপোর্ট জমা হয়েছে। অ্যাডমিন চেক করে ব্যালেন্স দিয়ে দিবে।")

# --- 👑 ADMIN SYSTEM (FULL POWER) ---

@bot.message_handler(commands=['admin'])
def admin_access(message):
    if message.from_user.id == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add("✅ Approve Bulk", "📊 Full Stats")
        markup.add("💰 Add Balance", "📜 Pending Reports")
        markup.add("🏠 Back to Menu")
        bot.send_message(message.chat.id, "👑 <b>অ্যাডমিন প্যানেলে স্বাগতম, তানজিম বস!</b>", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "❌ এক্সেস ডিনাইড!")

@bot.message_handler(func=lambda m: m.text == "📊 Full Stats" and m.from_user.id == ADMIN_ID)
def admin_stats(message):
    conn = sqlite3.connect("master_data.db")
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    total_u = cur.fetchone()[0]
    cur.execute("SELECT SUM(balance) FROM users")
    total_b = cur.fetchone()[0] or 0
    conn.close()
    
    bot.send_message(message.chat.id, f"📊 <b>বট স্ট্যাটাস:</b>\n\n👥 মোট ইউজার: {total_u}\n💰 মোট পেআউট বাকি: {total_b}৳")

@bot.message_handler(func=lambda m: m.text == "✅ Approve Bulk" and m.from_user.id == ADMIN_ID)
def bulk_approve_ui(message):
    msg = bot.send_message(message.chat.id, "📝 ইউজার আইডি বা ইউজারনেম লিস্ট দিন (এক লাইনে একটি):")
    bot.register_next_step_handler(msg, bulk_approve_logic)

def bulk_approve_logic(message):
    entries = message.text.split('\n')
    count = 0
    for e in entries:
        if e.strip():
            # এখানে অটো ব্যালেন্স অ্যাড করার কোড থাকবে
            count += 1
    bot.send_message(message.chat.id, f"🏁 সফলভাবে {count} টি রিপোর্ট অ্যাপ্রুভ করা হয়েছে।")

# ================= MISC BUTTONS =================

@bot.message_handler(func=lambda m: m.text == "💰 Balance")
def check_balance(message):
    conn = sqlite3.connect("master_data.db")
    cur = conn.cursor()
    cur.execute("SELECT balance FROM users WHERE user_id=?", (message.from_user.id,))
    res = cur.fetchone()
    bal = res[0] if res else 0
    conn.close()
    bot.send_message(message.chat.id, f"💰 Your balance: <b>${bal:.4f}</b>\n💰 Wallet ━━━━━━━━━━━━━━━━━━━━━━")

@bot.message_handler(func=lambda m: m.text == "📞 Support")
def support_info(message):
    bot.send_message(message.chat.id, f"━━━━━━━━━━━━━━━━━━━━━━\n🛠 Support: {SUPPORT_USER}\n━━━━━━━━━━━━━━━━━━━━━━")

# ================= WEB SERVER & RUN =================

@app.route('/')
def home(): return "Bot is Alive"
def run_web(): app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    t = Thread(target=run_web)
    t.start()
    logging.info("Bot is polling...")
    bot.infinity_polling()
        

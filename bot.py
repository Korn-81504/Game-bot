import sqlite3
import telebot
from telebot import types
import time
import random

# --- ตั้งค่า Bot Token ---
TOKEN = "8686238572:AAH0sS_cS1j6TXQo3ctuqMCjPNfzverzL9g"
bot = telebot.TeleBot(TOKEN)

# --- 1. ระบบฐานข้อมูล (SQLite) ---
def init_db():
    conn = sqlite3.connect('farm_game.db')
    c = conn.cursor()
    # ตารางผู้เล่น
    c.execute('''CREATE TABLE IF NOT EXISTS players 
                 (user_id TEXT PRIMARY KEY, name TEXT, money INTEGER, exp INTEGER, level INTEGER)''')
    # ตารางแปลงผัก
    c.execute('''CREATE TABLE IF NOT EXISTS plots 
                 (plot_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, crop_type TEXT, plant_time REAL)''')
    conn.commit()
    conn.close()

# --- 2. ข้อมูลผักและอีโมจิ ---
CROP_BOOK = {
    "basil": {"name": "กะเพรา", "emoji": "🌿", "time": 60, "buy": 50, "sell": 120},
    "tomato": {"name": "มะเขือเทศ", "emoji": "🍅", "time": 300, "buy": 150, "sell": 400},
    "melon": {"name": "เมล่อน", "emoji": "🍈", "time": 3600, "buy": 1000, "sell": 5000}
}

# --- 3. ฟังก์ชันจัดการข้อมูล (Database Logic) ---
def get_player(user_id):
    conn = sqlite3.connect('farm_game.db')
    c = conn.cursor()
    c.execute("SELECT * FROM players WHERE user_id=?", (str(user_id),))
    player = c.fetchone()
    conn.close()
    return player

def register_player(user_id, name):
    if not get_player(user_id):
        conn = sqlite3.connect('farm_game.db')
        c = conn.cursor()
        c.execute("INSERT INTO players VALUES (?, ?, ?, ?, ?)", (str(user_id), name, 500, 0, 1))
        conn.commit()
        conn.close()

# --- 4. คำสั่งบอท (Telegram Handlers) ---

@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    name = message.from_user.first_name
    register_player(uid, name)
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('🚜 ตรวจฟาร์ม', '🌱 ปลูกผัก', '💰 ร้านค้า')
    
    bot.send_message(message.chat.id, f"สวัสดี {name}! ฟาร์มของคุณเริ่มทำงานแล้ว!", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == '🚜 ตรวจฟาร์ม')
def check_farm(message):
    uid = str(message.from_user.id)
    conn = sqlite3.connect('farm_game.db')
    c = conn.cursor()
    c.execute("SELECT crop_type, plant_time FROM plots WHERE user_id=?", (uid,))
    my_plots = c.fetchall()
    conn.close()

    if not my_plots:
        bot.reply_to(message, "ฟาร์มว่างเปล่า... ไปปลูกผักกันเถอะ!")
        return

    report = "🚜 **สถานะแปลงผักของคุณ**\n\n"
    now = time.time()
    for crop_type, p_time in my_plots:
        crop = CROP_BOOK[crop_type]
        elapsed = now - p_time
        if elapsed >= crop['time']:
            report += f"{crop['emoji']} {crop['name']}: **เก็บเกี่ยวได้แล้ว!** /harvest\n"
        else:
            percent = int((elapsed / crop['time']) * 100)
            report += f"🌱 {crop['name']}: กำลังโต ({percent}%)\n"
    
    bot.send_message(message.chat.id, report, parse_mode="Markdown")

# --- รันบอท ---
if __name__ == "__main__":
    init_db() # สร้างฐานข้อมูลตอนเริ่ม
    print("บอทฟาร์มออนไลน์แล้ว...")
    bot.polling(none_stop=True)

import sqlite3
import json

DB_FILE = 'agent_database.db'

def init_db():
    """สร้างไฟล์ฐานข้อมูลและตารางเก็บแชท (ถ้ายังไม่มี)"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # สร้างตารางชื่อ user_chats เก็บ Username เป็นคีย์หลัก และเก็บแชทเป็นข้อความ
    c.execute('''CREATE TABLE IF NOT EXISTS user_chats 
                 (username TEXT PRIMARY KEY, chat_data TEXT)''')
    conn.commit()
    conn.close()

def load_chat_history(username):
    """โหลดประวัติแชทของ Username นั้นๆ ออกมาจากฐานข้อมูล"""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT chat_data FROM user_chats WHERE username=?", (username,))
        row = c.fetchone()
        conn.close()
        if row:
            return json.loads(row[0]) # แปลงข้อความกลับเป็น List แชท
        return []
    except Exception:
        return []

def save_chat_history(username, chat_data):
    """บันทึกประวัติแชทล่าสุดลงฐานข้อมูล"""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        chat_json = json.dumps(chat_data, ensure_ascii=False)
        # คำสั่ง REPLACE: ถ้ามีชื่อ user นี้แล้วให้เซฟทับ ถ้ายังไม่มีให้สร้างใหม่
        c.execute("REPLACE INTO user_chats (username, chat_data) VALUES (?, ?)", (username, chat_json))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error saving DB: {e}")
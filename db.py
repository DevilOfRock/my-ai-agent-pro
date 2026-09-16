import sqlite3
import json
from datetime import datetime

DB_FILE = 'agent_database.db'

def init_db():
    """สร้างตารางใหม่ รองรับระบบหลายห้องแชท"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # สร้างตาราง chat_sessions ที่มี session_id เป็นตัวแยกแยะแต่ละห้องแชท
    c.execute('''CREATE TABLE IF NOT EXISTS chat_sessions 
                 (session_id TEXT PRIMARY KEY, 
                  username TEXT, 
                  title TEXT, 
                  updated_at DATETIME, 
                  chat_data TEXT)''')
    conn.commit()
    conn.close()

def get_recent_chats(username):
    """ดึงรายชื่อห้องแชททั้งหมดของ User เรียงจากใหม่ไปเก่า"""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT session_id, title FROM chat_sessions WHERE username=? ORDER BY updated_at DESC", (username,))
        rows = c.fetchall()
        conn.close()
        # ส่งกลับเป็น List ของ Dictionary เพื่อเอาไปสร้างปุ่มในหน้าเว็บ
        return [{"session_id": r[0], "title": r[1]} for r in rows]
    except Exception:
        return []

def load_chat_session(session_id):
    """โหลดข้อมูลแชท (ข้อความ) จาก ID ห้องนั้นๆ"""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT chat_data FROM chat_sessions WHERE session_id=?", (session_id,))
        row = c.fetchone()
        conn.close()
        if row:
            return json.loads(row[0])
        return []
    except Exception:
        return []

def save_chat_session(session_id, username, title, chat_data):
    """บันทึกหรืออัปเดตห้องแชท"""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        chat_json = json.dumps(chat_data, ensure_ascii=False)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # คำสั่ง REPLACE: ถ้ามี session_id นี้แล้วให้อัปเดต ถ้ายังไม่มีให้สร้างบรรทัดใหม่
        c.execute('''REPLACE INTO chat_sessions (session_id, username, title, updated_at, chat_data) 
                     VALUES (?, ?, ?, ?, ?)''', (session_id, username, title, now, chat_json))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error saving DB: {e}")

def delete_chat_session(session_id):
    """ลบห้องแชททิ้ง (เตรียมเผื่อไว้ใช้ทำปุ่มลบแชท)"""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("DELETE FROM chat_sessions WHERE session_id=?", (session_id,))
        conn.commit()
        conn.close()
    except Exception:
        pass
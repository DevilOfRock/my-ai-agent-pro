import sqlite3
import json
import uuid
from datetime import datetime

DB_FILE = 'agent_database.db'

def init_db():
    """สร้างตารางใหม่ชื่อ chat_sessions สำหรับรองรับ 1 User หลายห้องแชท"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS chat_sessions 
                 (chat_id TEXT PRIMARY KEY, 
                  username TEXT, 
                  title TEXT, 
                  chat_data TEXT, 
                  updated_at DATETIME)''')
    conn.commit()
    conn.close()

def get_recent_chats(username):
    """ดึงรายชื่อแชท (ID และ หัวข้อ) ของ User คนนั้นเรียงตามเวลาล่าสุด"""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT chat_id, title FROM chat_sessions WHERE username=? ORDER BY updated_at DESC", (username,))
        rows = c.fetchall()
        conn.close()
        # ส่งกลับเป็น List ของ Dictionary
        return [{"chat_id": row[0], "title": row[1]} for row in rows]
    except Exception as e:
        print(f"Error getting recent chats: {e}")
        return []

def load_chat_history(chat_id):
    """โหลดประวัติแชทของห้องแชทนั้นๆ ออกมา"""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT chat_data FROM chat_sessions WHERE chat_id=?", (chat_id,))
        row = c.fetchone()
        conn.close()
        if row and row[0]:
            return json.loads(row[0])
        return []
    except Exception as e:
        print(f"Error loading chat: {e}")
        return []

def save_chat_history(chat_id, username, title, chat_data):
    """บันทึกแชทใหม่ หรืออัปเดตข้อมูลแชทเดิม"""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        chat_json = json.dumps(chat_data, ensure_ascii=False)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # เช็คว่าเคยมีห้องแชท ID นี้ในระบบหรือยัง
        c.execute("SELECT chat_id FROM chat_sessions WHERE chat_id=?", (chat_id,))
        exists = c.fetchone()
        
        if exists:
            # ถ้ามีแล้ว -> ให้อัปเดตข้อมูลแชทและเวลา
            c.execute("UPDATE chat_sessions SET chat_data=?, updated_at=? WHERE chat_id=?", (chat_json, now, chat_id))
        else:
            # ถ้ายังไม่มี -> ให้สร้างห้องแชทใหม่
            c.execute("INSERT INTO chat_sessions (chat_id, username, title, chat_data, updated_at) VALUES (?, ?, ?, ?, ?)", 
                      (chat_id, username, title, chat_json, now))
                      
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error saving chat: {e}")

def generate_chat_id():
    """สร้างรหัสห้องแชทใหม่แบบสุ่ม (ไม่ซ้ำแน่นอน)"""
    return str(uuid.uuid4())

def delete_chat_history(chat_id):
    """ลบประวัติแชทออกจากฐานข้อมูลอย่างถาวร"""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("DELETE FROM chat_sessions WHERE chat_id=?", (chat_id,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error deleting chat: {e}")
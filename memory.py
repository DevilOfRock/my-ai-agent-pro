import json
import os

MEMORY_FILE = "knowledge.json"

def load_memory():
    """โหลดความจำจากไฟล์"""
    if not os.path.exists(MEMORY_FILE):
        return {}
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_memory(data):
    """บันทึกความจำลงไฟล์"""
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def check_memory(question):
    """เช็คว่ามีคำถามนี้ในความจำหรือไม่"""
    memory = load_memory()
    # ค้นหาแบบง่ายๆ ถ้ามีคำถามที่ตรงกันหรือคล้ายกันมาก
    for q, a in memory.items():
        if q in question or question in q:
            return a
    return None

def teach_memory(question, answer):
    """สอนความจำใหม่ให้ AI"""
    memory = load_memory()
    memory[question] = answer
    save_memory(memory)
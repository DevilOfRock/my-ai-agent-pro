import streamlit as st
import PyPDF2
import base64
import datetime
import urllib.parse as urlparse
from youtube_transcript_api import YouTubeTranscriptApi
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
from knowledge_db import add_to_knowledge_base, search_knowledge_base

from memory import check_memory, teach_memory

# --- ประกาศ Tools ---
search_tool = DuckDuckGoSearchRun()

@tool
def calculate_vat(price: float) -> str:
    """คำนวณราคาสินค้ารวมภาษี VAT 7%"""
    return f"ราคารวม VAT 7% คือ {price * 1.07:.2f} บาท"

# 🟢 เพิ่ม Tool สำหรับดึงเนื้อหา YouTube 🟢
@tool
def summarize_youtube(url: str) -> str:
    """ใช้ดึงข้อความ (Transcript) จากคลิป YouTube เมื่อผู้ใช้ส่งลิงก์มาให้สรุป"""
    try:
        parsed_url = urlparse.urlparse(url)
        video_id = None
        if "youtube.com" in parsed_url.netloc:
            video_id = urlparse.parse_qs(parsed_url.query).get("v", [None])[0]
        elif "youtu.be" in parsed_url.netloc:
            video_id = parsed_url.path[1:]
            
        if not video_id:
            return "ดึงเนื้อหาไม่ได้: ลิงก์ YouTube ไม่ถูกต้องครับ"

        # พยายามดึงซับภาษาไทยก่อน ถ้าไม่มีเอาภาษาอังกฤษ
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        try:
            transcript = transcript_list.find_transcript(['th', 'en'])
        except:
            transcript = transcript_list.find_transcript(['en'])
            
        fetched_data = transcript.fetch()
        full_text = " ".join([t['text'] for t in fetched_data])
        
        # ส่งข้อความกลับไปให้ AI สรุป (จำกัดคำไว้ป้องกันล้น)
        return f"[ข้อความในคลิป]: {full_text[:15000]}"
    except Exception as e:
        return f"ดึงเนื้อหาไม่ได้ (คลิปอาจไม่มี Subtitle ปิดไว้): {str(e)}"

# 🟢 เพิ่ม summarize_youtube เข้าไปในรายการอาวุธ 🟢
tools = [search_tool, calculate_vat, summarize_youtube]

def extract_text(resp):
    if isinstance(resp, str): return resp
    if isinstance(resp, list) and len(resp) > 0:
        if isinstance(resp[0], dict) and "text" in resp[0]:
            return resp[0]["text"]
    if hasattr(resp, "text"): return resp.text
    return str(resp)

def read_pdf(uploaded_file):
    try:
        reader = PyPDF2.PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted: text += extracted + "\n"
        return text[:15000] 
    except Exception as e:
        return f"เกิดข้อผิดพลาดในการอ่าน PDF: {e}"

def get_ai_response(api_key, sys_prompt, final_input, file_context="", image_data=None):
    try:
        # 🟢 1. ระบบเรียนรู้ด้วยตัวเอง (บันทึกลงสมองระยะยาว ChromaDB) 🟢
        if final_input.startswith("จดจำ:"):
            # ตัดคำว่า "จดจำ:" ออก แล้วเอาเนื้อหาที่เหลือไปเซฟ
            knowledge_text = final_input.replace("จดจำ:", "").strip()
            add_to_knowledge_base(knowledge_text, source_name="ผู้ใช้สอน")
            return f"🧠 ผมได้เรียนรู้และจัดเก็บข้อมูลนี้ลงในสมองระยะยาวเรียบร้อยแล้วครับ!\n\n*(ข้อมูลที่บันทึก: {knowledge_text})*"

        # 🟢 2. ดึงความรู้จากสมองระยะยาวที่สอดคล้องกับคำถาม (RAG) 🟢
        retrieved_knowledge = search_knowledge_base(final_input)
        rag_context = ""
        if retrieved_knowledge:
            # ถ้าเจอข้อมูลที่ความหมายเกี่ยวข้องกัน ให้เตรียมข้อความไว้ป้อนให้ Gemini
            rag_context = f"\n\n[ข้อมูลเพิ่มเติมจากความทรงจำระยะยาวของคุณ]:\n{retrieved_knowledge}\n(จงใช้ข้อมูลนี้อ้างอิงในการตอบคำถามอย่างเป็นธรรมชาติ)"

        # --- จัดการเวลาของระบบ ---
        import datetime
        tz_th = datetime.timezone(datetime.timedelta(hours=7))
        current_time = datetime.datetime.now(tz_th).strftime("%Y-%m-%d %H:%M:%S")
        sys_prompt = f"[ข้อมูลระบบ: วันนี้คือวันที่และเวลา {current_time}]\n\n" + sys_prompt

        # --- รวมข้อมูลทั้งหมดเข้าด้วยกัน (คำถาม + ไฟล์อัปโหลด + ความจำระยะยาว) ---
        combined_prompt = final_input
        if file_context or rag_context:
            combined_prompt = f"คำถาม/คำสั่งของผู้ใช้: {final_input}\n\n[ข้อมูลอ้างอิงจากไฟล์]:\n{file_context}{rag_context}"

        # --- ตั้งค่าและเรียกใช้ Gemini API ---
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        
        print("👉 รันโค้ดใหม่แล้วโว้ย!") # เติมบรรทัดนี้ลงไปเพื่อจับผิด
        model = genai.GenerativeModel('gemini-1.5-flash') 

        if image_data:
            part = {"mime_type": "image/jpeg", "data": image_data}
            response = model.generate_content([sys_prompt, part, combined_prompt])
        else:
            response = model.generate_content([sys_prompt, combined_prompt])

        return response.text

    except Exception as e:
        return f"เกิดข้อผิดพลาดในการประมวลผล AI: {e}"
import streamlit as st
import PyPDF2
import base64
import datetime
import urllib.parse as urlparse
from youtube_transcript_api import YouTubeTranscriptApi
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool

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
        # เวลาของระบบ
        tz_th = datetime.timezone(datetime.timedelta(hours=7))
        current_time = datetime.datetime.now(tz_th).strftime("%Y-%m-%d %H:%M:%S")
        sys_prompt = f"[ข้อมูลระบบ: วันนี้คือวันที่และเวลา {current_time}]\n\n" + sys_prompt

        # ระบบจำ (Memory)
        if final_input.startswith("สอนAI:"):
            parts = final_input.replace("สอนAI:", "").split("=")
            if len(parts) == 2:
                teach_memory(parts[0].strip(), parts[1].strip())
                return f"🧠 จำไว้แล้วครับ! ถ้ามีคนถามว่า '{parts[0].strip()}' ผมจะตอบว่า '{parts[1].strip()}' ทันทีครับ"
            else:
                return "รูปแบบการสอนไม่ถูกต้องครับ ลอง: สอนAI: คำถาม = คำตอบ"

        cached_answer = check_memory(final_input)
        if cached_answer:
            return f"⚡ [ตอบจากความจำ]: {cached_answer}"

        # บริบทจากไฟล์
        if file_context:
            sys_prompt += f"\n\n[ข้อมูลอ้างอิงจากไฟล์เอกสารที่อัปโหลด: ให้ตอบคำถามโดยอิงจากข้อมูลต่อไปนี้]\n{file_context}"

        llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash", google_api_key=api_key)
        llm_with_tools = llm.bind_tools(tools)
        
        messages_payload = [("system", sys_prompt)]
        
        for i, msg in enumerate(st.session_state.chat_history):
            if i == len(st.session_state.chat_history) - 1 and image_data and msg["role"] == "user":
                b64_img = base64.b64encode(image_data).decode('utf-8')
                user_content = [
                    {"type": "text", "text": msg["content"]},
                    {"type": "image_url", "image_url": f"data:image/jpeg;base64,{b64_img}"}
                ]
                messages_payload.append(("user", user_content))
            else:
                messages_payload.append((msg["role"], msg["content"]))

        response = llm_with_tools.invoke(messages_payload)
        
        # 🟢 ดักจับ Tool ใหม่ตอน AI เรียกใช้งาน 🟢
        if response.tool_calls:
            tc = response.tool_calls[0]
            if tc["name"] == "duckduckgo_search":
                query = tc["args"].get("query", final_input)
                sr = search_tool.invoke(query)
                summary = llm.invoke(f"จากข้อมูล: {sr} จงตอบ: {final_input} เป็นภาษา {st.session_state.language}")
                return extract_text(summary.content)
            elif tc["name"] == "calculate_vat":
                return calculate_vat.invoke({"price": tc["args"].get("price", 0)})
            elif tc["name"] == "summarize_youtube":
                # ให้ดึงข้อมูลคลิปแล้วส่งให้ AI สรุปอีกที
                clip_data = summarize_youtube.invoke({"url": tc["args"].get("url", "")})
                summary = llm.invoke(f"จากเนื้อหาคลิปต่อไปนี้: {clip_data}\n\nคำสั่งจากผู้ใช้: {final_input}\nช่วยตอบเป็นภาษา {st.session_state.language} ให้อ่านง่ายๆ")
                return extract_text(summary.content)
        else:
            return extract_text(response.content)
            
    except Exception as e:
        return f"เกิดข้อผิดพลาด: {e}"
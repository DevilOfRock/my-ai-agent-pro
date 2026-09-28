import google.generativeai as genai
import PyPDF2
import base64
import datetime
import urllib.parse as urlparse
from youtube_transcript_api import YouTubeTranscriptApi
from duckduckgo_search import DDGS

from knowledge_db import add_to_knowledge_base, search_knowledge_base
from memory import check_memory, teach_memory

# --- 🛠️ ประกาศเครื่องมือ (Tools) ---

def search_web(query: str) -> str:
    """ใช้ค้นหาข้อมูลที่เป็นปัจจุบัน ข่าวสาร ราคาหุ้น ทองคำ หรือสิ่งที่ไม่รู้จากอินเทอร์เน็ต"""
    try:
        results = DDGS().text(query, max_results=3)
        if not results:
            return "ไม่พบข้อมูลบนอินเทอร์เน็ต"
        return str(results)
    except Exception as e:
        return f"ระบบค้นหามีปัญหา: {e}"

def calculate_vat(price: float) -> str:
    """คำนวณราคาสินค้ารวมภาษี VAT 7%"""
    return f"ราคารวม VAT 7% คือ {price * 1.07:.2f} บาท"

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

        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        try:
            transcript = transcript_list.find_transcript(['th', 'en'])
        except:
            transcript = transcript_list.find_transcript(['en'])
            
        fetched_data = transcript.fetch()
        full_text = " ".join([t['text'] for t in fetched_data])
        return f"[ข้อความในคลิป]: {full_text[:15000]}"
    except Exception as e:
        return f"ดึงเนื้อหาไม่ได้ (คลิปอาจไม่มี Subtitle ปิดไว้): {str(e)}"

# 🟢 ฟังก์ชันวาดรูป 🟢
def generate_image_url(prompt_text: str) -> str:
    try:
        encoded_prompt = urlparse.quote(prompt_text)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"
        return f"🎨 นี่คือรูปภาพที่คุณสั่งครับ:\n\n![Generated Image]({image_url})"
    except Exception as e:
        return f"ไม่สามารถสร้างรูปภาพได้: {e}"

# --- ฟังก์ชันอ่านไฟล์ PDF ---
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


# --- 🧠 สมองหลักประมวลผล AI ---
def get_ai_response(api_key, sys_prompt, final_input, file_context="", image_data=None):
    try:
        # 🟢 0. ดักจับคำสั่งวาดรูปตรงๆ ป้องกัน AI มโนโม้ตอบ 🟢
        image_keywords = ["วาดรูป", "สร้างรูป", "เจนรูป", "ขอรูป", "วาดภาพ", "ขอภาพ"]
        if any(keyword in final_input for keyword in image_keywords):
            # สั่งให้ Gemini ช่วยแปลง Prompt คำสั่งเป็นภาษาอังกฤษสั้นๆ ชัดๆ ก่อนส่งไปเจนรูป
            genai.configure(api_key=api_key)
            translator_model = genai.GenerativeModel('gemini-3.5-flash')
            trans_res = translator_model.generate_content(
                f"Translate this image prompt into a detailed English image generation prompt (return only the English text): {final_input}"
            )
            english_prompt = trans_res.text.strip()
            return generate_image_url(english_prompt)

        # 🟢 1. ระบบเรียนรู้ด้วยตัวเอง (บันทึกลงสมองระยะยาว ChromaDB) 🟢
        if final_input.startswith("จดจำ:"):
            knowledge_text = final_input.replace("จดจำ:", "").strip()
            add_to_knowledge_base(knowledge_text, source_name="ผู้ใช้สอน")
            return f"🧠 ผมได้เรียนรู้และจัดเก็บข้อมูลนี้ลงในสมองระยะยาวเรียบร้อยแล้วครับ!\n\n*(ข้อมูลที่บันทึก: {knowledge_text})*"

        # 🟢 2. ดึงความรู้จากสมองระยะยาวที่สอดคล้องกับคำถาม (RAG) 🟢
        retrieved_knowledge = search_knowledge_base(final_input)
        rag_context = ""
        if retrieved_knowledge:
            rag_context = f"\n\n[ข้อมูลเพิ่มเติมจากความทรงจำระยะยาวของคุณ]:\n{retrieved_knowledge}\n(จงใช้ข้อมูลนี้อ้างอิงในการตอบคำถามอย่างเป็นธรรมชาติ)"

        # --- จัดการเวลาของระบบ ---
        tz_th = datetime.timezone(datetime.timedelta(hours=7))
        current_time = datetime.datetime.now(tz_th).strftime("%Y-%m-%d %H:%M:%S")
        sys_prompt = f"[ข้อมูลระบบ: วันนี้คือวันที่และเวลา {current_time}]\n\n" + sys_prompt

        # --- รวมข้อมูลทั้งหมดเข้าด้วยกัน ---
        combined_prompt = final_input
        if file_context or rag_context:
            combined_prompt = f"คำถาม/คำสั่งของผู้ใช้: {final_input}\n\n[ข้อมูลอ้างอิงจากไฟล์]:\n{file_context}{rag_context}"
        
        full_message = f"{sys_prompt}\n\n{combined_prompt}"

        # --- ตั้งค่าและเรียกใช้ Gemini API ---
        genai.configure(api_key=api_key)
        
        model = genai.GenerativeModel(
            model_name='gemini-3.5-flash',
            tools=[search_web, calculate_vat, summarize_youtube]
        )
        
        chat = model.start_chat(enable_automatic_function_calling=True)

        if image_data:
            part = {"mime_type": "image/jpeg", "data": image_data}
            response = chat.send_message([part, full_message])
        else:
            response = chat.send_message(full_message)

        return response.text

    except Exception as e:
        return f"เกิดข้อผิดพลาดในการประมวลผล AI: {e}"
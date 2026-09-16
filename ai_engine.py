import streamlit as st
import PyPDF2
import base64
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool

# นำเข้าระบบความจำที่เราเพิ่งสร้าง
from memory import check_memory, teach_memory

# --- ประกาศ Tools ---
search_tool = DuckDuckGoSearchRun()

@tool
def calculate_vat(price: float) -> str:
    """คำนวณราคาสินค้ารวมภาษี VAT 7%"""
    return f"ราคารวม VAT 7% คือ {price * 1.07:.2f} บาท"

tools = [search_tool, calculate_vat]

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

# 🟢 เพิ่มตัวแปร image_data เพื่อรับรูปภาพ 🟢
def get_ai_response(api_key, sys_prompt, final_input, file_context="", image_data=None):
    try:
        # 1. ระบบจำ (Memory)
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

        # 2. จัดเตรียมบริบทจาก PDF (ถ้ามี)
        if file_context:
            sys_prompt += f"\n\n[ข้อมูลอ้างอิงจากไฟล์เอกสารที่อัปโหลด: ให้ตอบคำถามโดยอิงจากข้อมูลต่อไปนี้]\n{file_context}"

        llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash", google_api_key=api_key)
        llm_with_tools = llm.bind_tools(tools)
        
        # 3. สร้าง Payload ข้อความส่งให้ AI
        messages_payload = [("system", sys_prompt)]
        
        for i, msg in enumerate(st.session_state.chat_history):
            # 🟢 ถ้าเป็นข้อความล่าสุดและมีรูปภาพแนบมาด้วย ให้รวมรูปภาพส่งไปด้วย 🟢
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
        
        if response.tool_calls:
            tc = response.tool_calls[0]
            if tc["name"] == "duckduckgo_search":
                query = tc["args"].get("query", final_input)
                sr = search_tool.invoke(query)
                summary = llm.invoke(f"จากข้อมูล: {sr} จงตอบ: {final_input} เป็นภาษา {st.session_state.language}")
                return extract_text(summary.content)
            elif tc["name"] == "calculate_vat":
                return calculate_vat.invoke({"price": tc["args"].get("price", 0)})
        else:
            return extract_text(response.content)
            
    except Exception as e:
        return f"เกิดข้อผิดพลาด: {e}"
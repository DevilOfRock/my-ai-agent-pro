import streamlit as st
import PyPDF2
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool

# --- ประกาศ Tools ---
search_tool = DuckDuckGoSearchRun()

@tool
def calculate_vat(price: float) -> str:
    """คำนวณราคาสินค้ารวมภาษี VAT 7%"""
    return f"ราคารวม VAT 7% คือ {price * 1.07:.2f} บาท"

tools = [search_tool, calculate_vat]

def extract_text(resp):
    """ฟังก์ชันดึงข้อความจากผลลัพธ์ AI"""
    if isinstance(resp, str):
        return resp
    if isinstance(resp, list) and len(resp) > 0:
        if isinstance(resp[0], dict) and "text" in resp[0]:
            return resp[0]["text"]
    if hasattr(resp, "text"):
        return resp.text
    return str(resp)

def read_pdf(uploaded_file):
    """ฟังก์ชันสกัดข้อความจากไฟล์ PDF"""
    try:
        reader = PyPDF2.PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        # จำกัดตัวอักษรไม่ให้ยาวเกินโควต้าหน่วยความจำของ AI
        return text[:15000] 
    except Exception as e:
        return f"เกิดข้อผิดพลาดในการอ่าน PDF: {e}"

def get_ai_response(api_key, sys_prompt, final_input, file_context=""):
    """ฟังก์ชันส่งคำถามให้ AI ประมวลผล"""
    try:
        # หากมีการอัปโหลดไฟล์ ให้ยัดข้อมูลไฟล์เข้าไปเป็นความรู้พื้นฐานให้ AI
        if file_context:
            sys_prompt += f"\n\n[ข้อมูลอ้างอิงจากไฟล์เอกสารที่ผู้ใช้อัปโหลด: ให้ตอบคำถามโดยอิงจากข้อมูลต่อไปนี้เป็นหลัก]\n{file_context}"

        # แก้ไขชื่อโมเดลเป็น gemini-1.5-flash ที่ถูกต้อง
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key)
        llm_with_tools = llm.bind_tools(tools)
        
        messages_payload = [("system", sys_prompt)] + [(msg["role"], msg["content"]) for msg in st.session_state.chat_history]
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
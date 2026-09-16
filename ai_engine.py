import streamlit as st
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
    # ถ้าเป็น String อยู่แล้ว ให้ส่งคืนเลย
    if isinstance(resp, str):
        return resp
    # ถ้ามาเป็น List ที่มี Dictionary อยู่ข้างใน (เช่น กรณีใช้ Tools)
    if isinstance(resp, list) and len(resp) > 0:
        if isinstance(resp[0], dict) and "text" in resp[0]:
            return resp[0]["text"]
    # ถ้ามี attribute .text
    if hasattr(resp, "text"):
        return resp.text
    # ท้ายที่สุดถ้าไม่ตรงเงื่อนไขบน ค่อยแปลงเป็น String
    return str(resp)

def get_ai_response(api_key, sys_prompt, final_input):
    """ฟังก์ชันส่งคำถามให้ AI ประมวลผลแล้วส่งคำตอบกลับมา"""
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash", google_api_key=api_key)
        llm_with_tools = llm.bind_tools(tools)
        
        # แนบประวัติการคุยเข้าไปด้วย
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
import os
import streamlit as st
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool

# --- 1. Import โค้ดจากไฟล์ที่เราแยกไว้ ---
from ui_config import setup_page, load_css
from translations import i18n

load_dotenv()
# --- ดึง API KEY ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except Exception:
    api_key = os.getenv("GOOGLE_API_KEY")

# เรียกฟังก์ชันตั้งค่าหน้าเว็บ (จาก ui_config.py)
setup_page()

# --- 2. ระบบจัดการ State ---
if "theme" not in st.session_state: st.session_state.theme = "Dark" 
if "language" not in st.session_state: st.session_state.language = "ไทย"
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "current_user" not in st.session_state: st.session_state.current_user = ""
if "chat_history" not in st.session_state: st.session_state.chat_history = []

txt = i18n[st.session_state.language]

# โหลด CSS ตาม Theme (จาก ui_config.py)
load_css(st.session_state.theme)

# --- ดึง USER / PASSWORD ---
try:
    valid_user = st.secrets["APP_USER"]
    valid_pass = st.secrets["APP_PASS"]
except Exception:
    valid_user = os.getenv("APP_USER", "parinya_nnk")
    valid_pass = os.getenv("APP_PASS", "g@?OfEB8-q9X")

# --- 3. ระบบ LOGIN ---
if not st.session_state.logged_in:
    st.markdown(f"<h2 style='text-align: center; margin-top: 3rem;'>{txt['login_title']}</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username").strip()
            password = st.text_input("Password", type="password").strip()
            st.write("")
            login_submitted = st.form_submit_button("Log In", use_container_width=True)
            
            if login_submitted:
                if username == str(valid_user).strip() and password == str(valid_pass).strip():
                    st.session_state.logged_in = True
                    st.session_state.current_user = username
                    st.rerun()
                else:
                    st.error("Username หรือ Password ไม่ถูกต้อง")
        
        st.write("---")
        sel_lang = st.selectbox(txt["lang_label"], ["ไทย", "English", "中文"], index=["ไทย", "English", "中文"].index(st.session_state.language))
        if sel_lang != st.session_state.language:
            st.session_state.language = sel_lang
            st.rerun()

        sel_theme = st.radio(txt["theme_label"], ["Light", "Dark"], horizontal=True, index=0 if st.session_state.theme == "Light" else 1)
        if sel_theme != st.session_state.theme:
            st.session_state.theme = sel_theme
            st.rerun()
            
    st.stop()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.subheader("✨ AI Agent Pro")
    if st.button(txt["new_chat"], use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()
        
    if st.session_state.chat_history:
        chat_export = "".join([f"{'User' if msg['role'] == 'user' else 'AI'}: {msg['content']}\n\n" for msg in st.session_state.chat_history])
        st.download_button(label="💾 ดาวน์โหลดประวัติแชท", data=chat_export, file_name="chat_history.txt", mime="text/plain", use_container_width=True)
    
    st.divider()
    st.caption(txt["settings"])
    
    selected_lang = st.selectbox(txt["lang_label"], ["ไทย", "English", "中文"], key="sb_lang", index=["ไทย", "English", "中文"].index(st.session_state.language))
    if selected_lang != st.session_state.language:
        st.session_state.language = selected_lang
        st.rerun()
        
    selected_theme = st.radio(txt["theme_label"], ["Light", "Dark"], key="sb_theme", horizontal=True, index=0 if st.session_state.theme == "Light" else 1)
    if selected_theme != st.session_state.theme:
        st.session_state.theme = selected_theme
        st.rerun()

    st.divider()
    st.caption(f"Account: **{st.session_state.current_user}**")
    if st.button(txt["logout"], use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.current_user = ""
        st.rerun()

# --- 5. TOOLS & AI LOGIC ---
search_tool = DuckDuckGoSearchRun()

@tool
def calculate_vat(price: float) -> str:
    """คำนวณราคาสินค้ารวมภาษี VAT 7%"""
    return f"ราคารวม VAT 7% คือ {price * 1.07:.2f} บาท"

tools = [search_tool, calculate_vat]

def extract_text(resp):
    if hasattr(resp, "text"): return resp.text
    return str(resp)

# ระบบ Quick Prompts
prompt_to_send = None
if not st.session_state.chat_history:
    st.markdown(f"<div class='greeting-title'>{txt['greeting']}</div>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray; margin-bottom: 2rem;'>✨ เลือกคำถามด่วนด้านล่าง หรือพิมพ์คำถามของคุณเองได้เลย</p>", unsafe_allow_html=True)
    q_col1, q_col2, q_col3 = st.columns(3)
    if q_col1.button("📰 อัปเดตข่าวเทคโนโลยี", use_container_width=True): prompt_to_send = "ช่วยสรุปข่าวเทคโนโลยีที่น่าสนใจในช่วงนี้ให้ฟังหน่อย"
    if q_col2.button("⛅ เช็คสภาพอากาศ", use_container_width=True): prompt_to_send = "สภาพอากาศในกรุงเทพวันนี้เป็นอย่างไรบ้าง?"
    if q_col3.button("📧 ช่วยร่างอีเมล", use_container_width=True): prompt_to_send = "ช่วยร่างอีเมลขอนัดประชุมงานกับลูกค้าอย่างสุภาพให้หน่อย"

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input(txt["input_placeholder"])
final_input = prompt_to_send or user_input

if final_input:
    st.session_state.chat_history.append({"role": "user", "content": final_input})
    with st.chat_message("user"): st.markdown(final_input)

    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            try:
                llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash", google_api_key=api_key)
                llm_with_tools = llm.bind_tools(tools)
                
                messages_payload = [("system", txt["sys_prompt"])] + [(msg["role"], msg["content"]) for msg in st.session_state.chat_history]
                response = llm_with_tools.invoke(messages_payload)
                
                if response.tool_calls:
                    tc = response.tool_calls[0]
                    if tc["name"] == "duckduckgo_search":
                        query = tc["args"].get("query", final_input)
                        sr = search_tool.invoke(query)
                        summary = llm.invoke(f"จากข้อมูล: {sr} จงตอบ: {final_input} เป็นภาษา {st.session_state.language}")
                        final_text = extract_text(summary.content)
                    elif tc["name"] == "calculate_vat":
                        final_text = calculate_vat.invoke({"price": tc["args"].get("price", 0)})
                else:
                    final_text = extract_text(response.content)

                st.markdown(final_text)
                st.session_state.chat_history.append({"role": "assistant", "content": final_text})
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {e}")
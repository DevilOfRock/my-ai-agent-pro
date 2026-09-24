import os
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from streamlit_mic_recorder import speech_to_text

from ui_config import setup_page, load_css
from translations import i18n
from auth import init_session_state as auth_init_session, show_login_page, logout_user
from ai_engine import get_ai_response, read_pdf
from db import init_db, get_recent_chats, load_chat_history, save_chat_history, generate_chat_id, delete_chat_history

setup_page()

def init_chat_session():
    auth_init_session()
    if "current_chat_id" not in st.session_state:
        st.session_state.current_chat_id = generate_chat_id()
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

init_chat_session()
init_db()
load_dotenv()

txt = i18n[st.session_state.language]
load_css(st.session_state.theme)

file_context = ""
image_data = None

# --- SIDEBAR (แถบเมนูด้านซ้าย) ---
with st.sidebar:
    st.subheader("✨ AI Agent Pro")
    
    if st.session_state.logged_in:
        if st.button("➕ " + txt.get("new_chat", "เริ่มแชทใหม่"), use_container_width=True):
            st.session_state.current_chat_id = generate_chat_id()
            st.session_state.chat_history = []
            st.rerun()
            
        st.divider()
        
        # 🟢 เมนู Recents 🟢
        st.caption("🕒 ประวัติการคุย (Recents)")
        recent_chats = get_recent_chats(st.session_state.current_user)
        
        if not recent_chats:
            st.markdown("<p style='font-size: 0.8rem; color: gray;'>ยังไม่มีประวัติการคุย</p>", unsafe_allow_html=True)
        else:
            for chat in recent_chats:
                col_title, col_menu = st.columns([5, 1])
                
                with col_title:
                    if st.button(f"💬 {chat['title']}", key=f"btn_{chat['chat_id']}", use_container_width=True):
                        st.session_state.current_chat_id = chat['chat_id']
                        st.session_state.chat_history = load_chat_history(chat['chat_id'])
                        st.rerun()
                
                with col_menu:
                    with st.popover("⋮", use_container_width=True):
                        if st.button("🗑️ ลบแชท", key=f"del_{chat['chat_id']}", use_container_width=True):
                            delete_chat_history(chat['chat_id'])
                            if st.session_state.current_chat_id == chat['chat_id']:
                                st.session_state.current_chat_id = generate_chat_id()
                                st.session_state.chat_history = []
                            st.rerun()
        
        st.divider()

        # 🟢 ระบบอัปโหลดและดูดไฟล์ลงสมอง RAG 🟢
        uploaded_file = st.file_uploader("อัปโหลด (PDF, PNG, JPG, CSV, Excel)", type=['pdf', 'png', 'jpg', 'jpeg', 'csv', 'xlsx'])

        if uploaded_file:
            if uploaded_file.name.lower().endswith('.pdf'):
                if st.button("🧠 ดูดไฟล์นี้ลงสมองระยะยาว (RAG)", use_container_width=True):
                    with st.status("กำลังย่อยและบันทึกข้อมูลลงสมอง..."):
                        # ดึงฟังก์ชันอ่าน PDF มาใช้
                        pdf_text = read_pdf(uploaded_file)
                        
                        # ทำ Chunking: หั่นข้อความยาวๆ เป็นท่อน ท่อนละ 1,000 ตัวอักษร
                        chunk_size = 1000
                        chunks = [pdf_text[i:i + chunk_size] for i in range(0, len(pdf_text), chunk_size)]
                        
                        from knowledge_db import add_to_knowledge_base
                        for i, chunk in enumerate(chunks):
                            # โยนแต่ละท่อนเข้าตู้ความจำ
                            add_to_knowledge_base(chunk, source_name=f"ไฟล์ {uploaded_file.name} (ส่วนที่ {i+1})")
                        
                    st.success(f"บันทึกความรู้จาก {uploaded_file.name} ลงสมองสำเร็จ! (รวม {len(chunks)} ส่วน)")
        
        st.divider()

    # 🟢 การตั้งค่า (จับกลับเข้ามาใน Sidebar) 🟢
    st.caption(txt.get("settings", "การตั้งค่า"))
    selected_lang = st.selectbox(txt.get("lang_label", "ภาษา"), ["ไทย", "English", "中文"], key="sb_lang", index=["ไทย", "English", "中文"].index(st.session_state.language))
    if selected_lang != st.session_state.language:
        st.session_state.language = selected_lang
        st.rerun()
        
    selected_theme = st.radio(txt.get("theme_label", "โหมดสี"), ["Light", "Dark"], key="sb_theme", horizontal=True, index=0 if st.session_state.theme == "Light" else 1)
    if selected_theme != st.session_state.theme:
        st.session_state.theme = selected_theme
        st.rerun()

    if st.session_state.logged_in:
        st.divider()
        st.caption(f"Account: **{st.session_state.current_user}**")
        if st.button(txt.get("logout", "ออกจากระบบ"), use_container_width=True):
            logout_user()
            if "current_chat_id" in st.session_state:
                del st.session_state["current_chat_id"]
            st.rerun()

# --- เช็คล็อกอิน ---
if not show_login_page(txt):
    st.stop()

try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except Exception:
    api_key = os.getenv("GOOGLE_API_KEY")

# --- ส่วนห้องแชทหลัก ---
prompt_to_send = None
if not st.session_state.chat_history:
    st.markdown(f"<div class='greeting-title'>{txt.get('greeting', 'ยินดีต้อนรับ')}</div>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray; margin-bottom: 2rem;'>✨ เลือกคำถามด่วนด้านล่าง หรือพิมพ์คำถามของคุณเองได้เลย</p>", unsafe_allow_html=True)
    
    q_col1, q_col2, q_col3 = st.columns(3)
    if q_col1.button("📰 อัปเดตข่าวเทคโนโลยี", use_container_width=True): prompt_to_send = "ช่วยสรุปข่าวเทคโนโลยีที่น่าสนใจในช่วงนี้ให้ฟังหน่อย"
    if q_col2.button("⛅ เช็คสภาพอากาศ", use_container_width=True): prompt_to_send = "สภาพอากาศในกรุงเทพวันนี้เป็นอย่างไรบ้าง?"
    if q_col3.button("📧 ช่วยร่างอีเมล", use_container_width=True): prompt_to_send = "ช่วยร่างอีเมลขอนัดประชุมงานกับลูกค้าอย่างสุภาพให้หน่อย"

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

voice_text = None
col_mic, col_space = st.columns([1, 4])
with col_mic:
    voice_text = speech_to_text(language='th', start_prompt="🎙️ พูดสั่งงาน", stop_prompt="⏹️ หยุดฟัง", key='voice_input')

user_input = st.chat_input(txt.get("input_placeholder", "พิมพ์ข้อความ..."))
final_input = prompt_to_send or voice_text or user_input

if final_input:
    st.session_state.chat_history.append({"role": "user", "content": final_input})
    with st.chat_message("user"): 
        st.markdown(final_input)

    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            final_text = get_ai_response(api_key, txt.get("sys_prompt", ""), final_input, file_context, image_data)
            st.markdown(final_text)
            st.session_state.chat_history.append({"role": "assistant", "content": final_text})
            
            chat_title = st.session_state.chat_history[0]["content"]
            if len(chat_title) > 30:
                chat_title = chat_title[:30] + "..."
            
            save_chat_history(st.session_state.current_chat_id, st.session_state.current_user, chat_title, st.session_state.chat_history)
            
            st.rerun()
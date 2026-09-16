import os
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from streamlit_mic_recorder import speech_to_text

from ui_config import setup_page, load_css
from translations import i18n
from auth import init_session_state, show_login_page, logout_user
from ai_engine import get_ai_response, read_pdf

from db import init_db, load_chat_history, save_chat_history

# 1. สั่งตั้งค่า Session และ DB
setup_page()
init_session_state()
init_db()
load_dotenv()

txt = i18n[st.session_state.language]
load_css(st.session_state.theme)

file_context = ""
image_data = None

# --- 2. SIDEBAR (จัดเรียงลำดับให้เหมือนเดิม) ---
with st.sidebar:
    st.subheader("✨ AI Agent Pro")
    
    # 🟢 โชว์ปุ่มแชทใหม่และกล่องอัปโหลด *เฉพาะตอนล็อกอินแล้ว* ไว้ด้านบน 🟢
    if st.session_state.logged_in:
        if st.button(txt["new_chat"], use_container_width=True):
            st.session_state.chat_history = []
            save_chat_history(st.session_state.current_user, [])
            st.rerun()
            
        if st.session_state.chat_history:
            chat_export = "".join([f"{'User' if msg['role'] == 'user' else 'AI'}: {msg['content']}\n\n" for msg in st.session_state.chat_history])
            st.download_button(label="💾 ดาวน์โหลดประวัติแชท", data=chat_export, file_name="chat_history.txt", mime="text/plain", use_container_width=True)
        
        st.divider()

        st.caption("📂 คลังความรู้ (PDF, รูปภาพ, ตารางข้อมูล)")
        uploaded_file = st.file_uploader("อัปโหลด (PDF, PNG, JPG, CSV, Excel)", type=["pdf", "png", "jpg", "jpeg", "csv", "xlsx"])
        
        if uploaded_file is not None:
            file_ext = uploaded_file.name.split('.')[-1].lower()
            with st.spinner("กำลังวิเคราะห์ไฟล์..."):
                if file_ext == "pdf":
                    file_context = read_pdf(uploaded_file)
                    st.success("อ่านไฟล์ PDF สำเร็จ!")
                elif file_ext in ["csv", "xlsx"]:
                    try:
                        if file_ext == "csv":
                            df = pd.read_csv(uploaded_file)
                        else:
                            df = pd.read_excel(uploaded_file)
                        
                        file_context = f"ข้อมูลจากไฟล์ตาราง ({uploaded_file.name}):\n{df.to_string()}"
                        st.success("อ่านข้อมูลตารางสำเร็จ!")
                        st.dataframe(df.head(5))
                    except Exception as e:
                        st.error(f"เกิดข้อผิดพลาดในการอ่านไฟล์ตาราง: {e}")
                else:
                    image_data = uploaded_file.getvalue()
                    st.image(uploaded_file, caption="อัปโหลดรูปภาพสำเร็จ!", use_container_width=True)
        
        st.divider()

    # 🟢 ส่วนการตั้งค่า โชว์เสมอ (ให้อยู่ตรงกลาง) 🟢
    st.caption(txt["settings"])
    selected_lang = st.selectbox(txt["lang_label"], ["ไทย", "English", "中文"], key="sb_lang", index=["ไทย", "English", "中文"].index(st.session_state.language))
    if selected_lang != st.session_state.language:
        st.session_state.language = selected_lang
        st.rerun()
        
    selected_theme = st.radio(txt["theme_label"], ["Light", "Dark"], key="sb_theme", horizontal=True, index=0 if st.session_state.theme == "Light" else 1)
    if selected_theme != st.session_state.theme:
        st.session_state.theme = selected_theme
        st.rerun()

    # 🟢 โชว์ปุ่มออกจากระบบ ไว้ล่างสุด *เฉพาะตอนล็อกอินแล้ว* 🟢
    if st.session_state.logged_in:
        st.divider()
        st.caption(f"Account: **{st.session_state.current_user}**")
        if st.button(txt["logout"], use_container_width=True):
            logout_user()
            st.rerun()

# --- 3. หยุดโค้ดตรงนี้ ถ้ายังไม่ล็อกอิน ---
if not show_login_page(txt):
    st.stop()


# --- 4. โค้ดห้องแชท (ทำงานเมื่อล็อกอินผ่านแล้ว) ---
if "db_loaded" not in st.session_state or not st.session_state.db_loaded:
    st.session_state.chat_history = load_chat_history(st.session_state.current_user)
    st.session_state.db_loaded = True

try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except Exception:
    api_key = os.getenv("GOOGLE_API_KEY")

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

voice_text = None
col_mic, col_space = st.columns([1, 4])
with col_mic:
    voice_text = speech_to_text(language='th', start_prompt="🎙️ พูดสั่งงาน", stop_prompt="⏹️ หยุดฟัง", key='voice_input')

user_input = st.chat_input(txt["input_placeholder"])
final_input = prompt_to_send or voice_text or user_input

if final_input:
    st.session_state.chat_history.append({"role": "user", "content": final_input})
    with st.chat_message("user"): 
        st.markdown(final_input)

    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            final_text = get_ai_response(api_key, txt["sys_prompt"], final_input, file_context, image_data)
            st.markdown(final_text)
            st.session_state.chat_history.append({"role": "assistant", "content": final_text})
            
            save_chat_history(st.session_state.current_user, st.session_state.chat_history)
import os
import streamlit as st
from dotenv import load_dotenv

from ui_config import setup_page, load_css
from translations import i18n
from auth import init_session_state, show_login_page
from ai_engine import get_ai_response, read_pdf

load_dotenv()

setup_page()
init_session_state()

txt = i18n[st.session_state.language]
load_css(st.session_state.theme)

if not show_login_page(txt):
    st.stop()

try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except Exception:
    api_key = os.getenv("GOOGLE_API_KEY")

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
    
    # 🟢 เพิ่มระบบอัปโหลดไฟล์ PDF 🟢
    st.caption("📂 คลังความรู้ (Knowledge Base)")
    uploaded_file = st.file_uploader("อัปโหลดไฟล์ PDF", type=["pdf"])
    file_context = ""
    if uploaded_file is not None:
        with st.spinner("กำลังวิเคราะห์ไฟล์..."):
            file_context = read_pdf(uploaded_file)
        st.success("อ่านไฟล์สำเร็จ! ถามเนื้อหาได้เลย")
    
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

# --- 5. หน้าแชทหลัก (Main Chat UI) ---
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
    with st.chat_message("user"): 
        st.markdown(final_input)

    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            # 🟢 ส่ง file_context ไปให้ AI Engine ประมวลผลร่วมกับคำถาม 🟢
            final_text = get_ai_response(api_key, txt["sys_prompt"], final_input, file_context)
            st.markdown(final_text)
            st.session_state.chat_history.append({"role": "assistant", "content": final_text})
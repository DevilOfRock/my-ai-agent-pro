import streamlit as st
import os

def init_session_state():
    """ฟังก์ชันตั้งค่าตัวแปรเริ่มต้น"""
    if "theme" not in st.session_state: st.session_state.theme = "Dark" 
    if "language" not in st.session_state: st.session_state.language = "ไทย"
    if "logged_in" not in st.session_state: st.session_state.logged_in = False
    if "current_user" not in st.session_state: st.session_state.current_user = ""
    if "chat_history" not in st.session_state: st.session_state.chat_history = []

def show_login_page(txt):
    """ฟังก์ชันแสดงหน้าล็อกอิน คืนค่า True ถ้าล็อกอินผ่านแล้ว"""
    if st.session_state.logged_in:
        return True

    try:
        valid_user = st.secrets["APP_USER"]
        valid_pass = st.secrets["APP_PASS"]
    except Exception:
        valid_user = os.getenv("APP_USER", "parinya_nnk")
        valid_pass = os.getenv("APP_PASS", "g@?OfEB8-q9X")

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
            
    return False
import streamlit as st
import extra_streamlit_components as stx
import datetime

# ตารางจำลองผู้ใช้งาน (ในระบบจริงสามารถดึงจาก DB ได้)
USERS = {
    "admin": "g@?OfEB8-q9X",
    "parinya_nnk": "g@?OfEB8-q9X"
}

def get_cookie_manager():
    if "cookie_manager" not in st.session_state:
        st.session_state.cookie_manager = stx.CookieManager(key="auth_cookies")
    return st.session_state.cookie_manager

def init_session_state():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "current_user" not in st.session_state:
        st.session_state.current_user = ""
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
        
    # 🟢 เพิ่มการตั้งค่าภาษาและธีมเริ่มต้นกลับเข้ามา
    if "language" not in st.session_state:
        st.session_state.language = "ไทย"
    if "theme" not in st.session_state:
        st.session_state.theme = "Dark"

def show_login_page(txt):
    cookie_manager = get_cookie_manager()
    
    # ดึงค่า User ที่เคยเซฟไว้ใน Cookie (ถ้ามี)
    auth_cookie = cookie_manager.get(cookie="logged_in_user")
    
    # ถ้ามี Cookie ค้างอยู่ ให้ล็อกอินให้อัตโนมัติทันที
    if auth_cookie and not st.session_state.logged_in:
        st.session_state.logged_in = True
        st.session_state.current_user = auth_cookie
        return True

    if st.session_state.logged_in:
        return True

    st.markdown(f"<h2 style='text-align: center;'>🔑 {txt.get('login_title', 'เข้าสู่ระบบ')}</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # 🟢 สร้าง Form เพื่อให้กด Enter ได้ (จัดให้อยู่ตรงกลาง) 🟢
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            # ปุ่ม submit สำหรับ form
            submitted = st.form_submit_button("เข้าสู่ระบบ", use_container_width=True)
            
            if submitted:
                # เช็ครหัสผ่านจากตาราง USERS ด้านบน
                if username in USERS and USERS[username] == password: 
                    st.session_state.logged_in = True
                    st.session_state.current_user = username
                    # เซฟคุกกี้ให้อยู่ในระบบ 30 วัน
                    cookie_manager.set("logged_in_user", username, expires_at=datetime.datetime.now() + datetime.timedelta(days=30))
                    st.rerun() # รีเฟรชหน้าเพื่อเข้าสู่แอป
                else:
                    st.error("Username หรือ Password ไม่ถูกต้อง")
                
    return False

def logout_user():
    """ฟังก์ชันเคลียร์สถานะตอนกดออกจากระบบ"""
    cookie_manager = get_cookie_manager()
    cookie_manager.delete("logged_in_user")
    st.session_state.logged_in = False
    st.session_state.current_user = ""
    st.session_state.chat_history = []
    if "db_loaded" in st.session_state:
        st.session_state.db_loaded = False
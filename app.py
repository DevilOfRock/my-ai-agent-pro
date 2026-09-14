import os
import streamlit as st
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool

load_dotenv()

# --- ดึง API KEY ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except Exception:
    api_key = os.getenv("GOOGLE_API_KEY")

st.set_page_config(page_title="AI Agent Pro", page_icon="✨", layout="wide")

# --- 1. ระบบจัดการ State ---
if "theme" not in st.session_state:
    st.session_state.theme = "Dark"  # ค่าเริ่มต้นเป็น Dark Mode

if "language" not in st.session_state:
    st.session_state.language = "ไทย"

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "current_user" not in st.session_state:
    st.session_state.current_user = ""

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- ดึง USER / PASSWORD ---
try:
    valid_user = st.secrets["APP_USER"]
    valid_pass = st.secrets["APP_PASS"]
except Exception:
    valid_user = os.getenv("APP_USER", "parinya_nnk")
    valid_pass = os.getenv("APP_PASS", "g@?OfEB8-q9X")

# --- 2. ข้อความสลับภาษา ---
i18n = {
    "ไทย": {
        "login_title": "✨ เข้าสู่ระบบ AI Agent Pro",
        "greeting": "Hi AI Agent Pro, let's get into it",
        "new_chat": "➕ เริ่มแชทใหม่",
        "settings": "⚙️ การตั้งค่า",
        "theme_label": "โทนสี (Theme)",
        "lang_label": "ภาษา (Language)",
        "logout": "🚪 ออกจากระบบ",
        "input_placeholder": "Ask AI Agent Pro...",
        "sys_prompt": "คุณคือ AI Agent Pro ผู้ช่วยอัจฉริยะ ตอบคำถามเป็นภาษาไทยอย่างสุภาพและเป็นกันเอง"
    },
    "English": {
        "login_title": "✨ AI Agent Pro Login",
        "greeting": "Hi AI Agent Pro, let's get into it",
        "new_chat": "➕ New Chat",
        "settings": "⚙️ Settings",
        "theme_label": "Theme",
        "lang_label": "Language",
        "logout": "🚪 Log Out",
        "input_placeholder": "Ask AI Agent Pro...",
        "sys_prompt": "You are AI Agent Pro, a smart assistant. Respond in English politely and naturally."
    },
    "中文": {
        "login_title": "✨ 登录 AI Agent Pro",
        "greeting": "Hi AI Agent Pro, let's get into it",
        "new_chat": "➕ 新建对话",
        "settings": "⚙️ 设置",
        "theme_label": "主题模式 (Theme)",
        "lang_label": "语言 (Language)",
        "logout": "🚪 退出登录",
        "input_placeholder": "Ask AI Agent Pro...",
        "sys_prompt": "你是 AI Agent Pro 智能助手。请使用中文礼貌自然地回答问题。"
    }
}

txt = i18n[st.session_state.language]

# --- 3. Dynamic CSS ---
if st.session_state.theme == "Light":
    # 1. โหมด Light: กลับมาใช้พื้นหลังสีฟ้าอ่อนแบบไล่สี (Gradient)
    app_bg = "radial-gradient(circle at top, #E8F0FE 0%, #F8FAFD 60%, #FFFFFF 100%)"
    text_color = "#1F2937"
    sidebar_bg = "#F0F4F9"
    input_bg = "#FFFFFF"     # พื้นหลังช่องพิมพ์สีขาว
    input_text = "#111827"   # ตัวหนังสือในช่องพิมพ์สีดำ
    user_bg = "#D2E3FC"
    user_text = "#111827"
    ai_bg = "#FFFFFF"
    border_color = "#C0C4CC"
else: 
    app_bg = "#0E1117"
    text_color = "#FAFAFA"
    sidebar_bg = "#262730"
    # 2. โหมด Dark: บังคับให้ช่องพิมพ์เป็นสีขาว และตัวหนังสือพิมพ์เป็นสีดำ
    input_bg = "#FFFFFF"     # พื้นหลังช่องพิมพ์เป็นสีขาว
    input_text = "#111827"   # ตัวหนังสือที่พิมพ์ต้องเป็นสีดำเท่านั้น จะได้อ่านชัดเจน
    user_bg = "#1A73E8"
    user_text = "#FFFFFF"
    ai_bg = "#262730"
    border_color = "#4B4C53"

st.markdown(f"""
    <style>
    /* พื้นหลังและตัวหนังสือหลัก */
    .stApp, .stApp > header {{
        background: {app_bg} !important;
        color: {text_color} !important;
    }}
    header {{ visibility: hidden; }}
    
    p, span, label, h1, h2, h3, h4, h5, h6 {{
        color: {text_color} !important;
    }}
    
    section[data-testid="stSidebar"] {{
        background-color: {sidebar_bg} !important;
        border-right: 1px solid {border_color} !important;
    }}
    
    /* แก้ไขปุ่มทั้งหมด */
    [data-testid="stFormSubmitButton"] > button, .stButton > button {{
        background-color: #1A73E8 !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        border: none !important;
    }}
    [data-testid="stFormSubmitButton"] p, .stButton p {{
        color: #FFFFFF !important;
    }}
    
    /* แก้ไขช่องกรอกข้อความและ Selectbox (บังคับพื้นหลังตามที่เราตั้ง) */
    div[data-baseweb="select"] > div, 
    div[data-baseweb="input"] > div, 
    .stTextInput div[data-baseweb="input"] {{
        background-color: {input_bg} !important;
        border: 1px solid {border_color} !important;
    }}
    
    /* บังคับสีข้อความในช่องกรอกให้เป็นสีดำเสมอ */
    div[data-baseweb="select"] span, 
    div[data-baseweb="input"] input, 
    div[data-testid="stChatInput"] textarea {{
        color: {input_text} !important;
        -webkit-text-fill-color: {input_text} !important;
    }}
    div[data-baseweb="select"] svg {{ fill: {input_text} !important; }}

    /* แก้แถบสีด้านล่างสุดของช่องพิมพ์แชทให้โปร่งใสกลืนกับพื้นหลังหลัก */
    [data-testid="stBottom"], [data-testid="stBottom"] > div {{
        background: transparent !important;
    }}
    
    /* กล่องพิมพ์แชท */
    div[data-testid="stChatInput"] {{
        background-color: {input_bg} !important;
        border: 1px solid {border_color} !important;
        border-radius: 20px !important;
    }}

    .greeting-title {{
        font-size: 2.8rem;
        font-weight: 400;
        color: {text_color};
        text-align: center;
        margin-top: 6rem;
        margin-bottom: 2rem;
        font-family: 'Google Sans', sans-serif, Segoe UI;
    }}
    
    /* --- จัดวาง Chat Bubbles (คนขวา, AI ซ้าย) --- */
    
    /* ข้อความฝั่ง User (คนพิมพ์) */
    div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {{
        flex-direction: row-reverse !important;
        background-color: {user_bg} !important;
        margin-left: auto !important;
        margin-right: 0 !important;
        border-radius: 20px 20px 4px 20px !important;
        padding: 1rem 1.5rem !important;
        max-width: 80% !important;
        border: none !important;
    }}
    /* สีข้อความของ User */
    div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) div[data-testid="stMarkdownContainer"] p {{
        color: {user_text} !important;
    }}
    
    /* ข้อความฝั่ง AI */
    div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {{
        flex-direction: row !important;
        background-color: {ai_bg} !important;
        margin-right: auto !important;
        margin-left: 0 !important;
        border-radius: 20px 20px 20px 4px !important;
        padding: 1rem 1.5rem !important;
        max-width: 80% !important;
        border: 1px solid {border_color} !important;
    }}
    </style>
""", unsafe_allow_html=True)

# --- 4. ระบบ LOGIN ---
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
        sel_lang = st.selectbox(
            txt["lang_label"],
            ["ไทย", "English", "中文"],
            index=["ไทย", "English", "中文"].index(st.session_state.language)
        )
        if sel_lang != st.session_state.language:
            st.session_state.language = sel_lang
            st.rerun()

        sel_theme = st.radio(
            txt["theme_label"],
            ["Light", "Dark"],
            horizontal=True,
            index=0 if st.session_state.theme == "Light" else 1
        )
        if sel_theme != st.session_state.theme:
            st.session_state.theme = sel_theme
            st.rerun()
            
    st.stop()

# --- 5. SIDEBAR ---
with st.sidebar:
    st.subheader("✨ AI Agent Pro")
    if st.button(txt["new_chat"], use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()
    
    st.divider()
    st.caption(txt["settings"])
    
    selected_lang = st.selectbox(
        txt["lang_label"],
        ["ไทย", "English", "中文"],
        key="sb_lang",
        index=["ไทย", "English", "中文"].index(st.session_state.language)
    )
    if selected_lang != st.session_state.language:
        st.session_state.language = selected_lang
        st.rerun()
        
    selected_theme = st.radio(
        txt["theme_label"],
        ["Light", "Dark"],
        key="sb_theme",
        horizontal=True,
        index=0 if st.session_state.theme == "Light" else 1
    )
    if selected_theme != st.session_state.theme:
        st.session_state.theme = selected_theme
        st.rerun()

    st.divider()
    st.caption(f"Account: **{st.session_state.current_user}**")
    if st.button(txt["logout"], use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.current_user = ""
        st.rerun()

# --- 6. TOOLS & AI LOGIC ---
search_tool = DuckDuckGoSearchRun()

@tool
def calculate_vat(price: float) -> str:
    """คำนวณราคาสินค้ารวมภาษี VAT 7%"""
    total = price * 1.07
    return f"ราคารวม VAT 7% คือ {total:.2f} บาท"

tools = [search_tool, calculate_vat]

def extract_text(response_content):
    if isinstance(response_content, str):
        return response_content
    if isinstance(response_content, list) and len(response_content) > 0:
        if isinstance(response_content[0], dict) and "text" in response_content[0]:
            return response_content[0]["text"]
    if hasattr(response_content, "text"):
        return response_content.text
    return str(response_content)

if not st.session_state.chat_history:
    st.markdown(f"<div class='greeting-title'>{txt['greeting']}</div>", unsafe_allow_html=True)

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_input := st.chat_input(txt["input_placeholder"]):
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            try:
                llm = ChatGoogleGenerativeAI(
                    model="gemini-3.6-flash",
                    google_api_key=api_key
                )
                llm_with_tools = llm.bind_tools(tools)
                
                messages_payload = [("system", txt["sys_prompt"])]
                for msg in st.session_state.chat_history:
                    messages_payload.append((msg["role"], msg["content"]))
                
                response = llm_with_tools.invoke(messages_payload)
                
                if response.tool_calls:
                    tool_call = response.tool_calls[0]
                    tool_name = tool_call["name"]
                    
                    if tool_name == "duckduckgo_search":
                        query = tool_call["args"].get("query", user_input)
                        search_result = search_tool.invoke(query)
                        summary_response = llm.invoke(f"จากข้อมูล: {search_result} จงตอบคำถาม: {user_input} เป็นภาษา {st.session_state.language}")
                        final_text = extract_text(summary_response.content)
                    elif tool_name == "calculate_vat":
                        price_arg = tool_call["args"].get("price", 0)
                        final_text = calculate_vat.invoke({"price": price_arg})
                else:
                    final_text = extract_text(response.content)

                st.markdown(final_text)
                st.session_state.chat_history.append({"role": "assistant", "content": final_text})

            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {e}")
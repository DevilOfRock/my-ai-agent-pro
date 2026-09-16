import streamlit as st

def setup_page():
    st.set_page_config(page_title="AI Agent Pro", page_icon="✨", layout="wide")

def load_css(theme):
    if theme == "Light":
        app_bg = "radial-gradient(circle at top, #E8F0FE 0%, #F8FAFD 60%, #FFFFFF 100%)"
        text_color = "#1F2937"
        sidebar_bg = "#F0F4F9"
        input_bg = "#FFFFFF"     
        input_text = "#111827"   
        user_bg = "#D2E3FC"
        user_text = "#111827"
        ai_bg = "#FFFFFF"
        ai_text = "#1F2937"
        border_color = "#C0C4CC"
    else: 
        app_bg = "#0E1117"
        text_color = "#FAFAFA"
        sidebar_bg = "#262730"
        input_bg = "#FFFFFF"     
        input_text = "#111827"   
        user_bg = "#1A73E8"
        user_text = "#FFFFFF"
        ai_bg = "#262730"
        ai_text = "#FAFAFA"
        border_color = "#4B4C53"

    st.markdown(f"""
        <style>
        /* 1. ตั้งค่าสีพื้นหลังหลักของแอป */
        .stApp {{ background: {app_bg} !important; }}
        
        /* 2. ทำให้แถบ Header โปร่งใส */
        header[data-testid="stHeader"] {{ background: transparent !important; }}
        
        /* 3. ซ่อนเมนูด้านขวาบน (Deploy / จุด 3 จุด) ไม่ให้มารกสายตา */
        [data-testid="stToolbar"], [data-testid="stHeaderActionElements"] {{ display: none !important; }}
        
        /* 4. 🟢 บังคับปุ่มกางเมนู Sidebar ให้โผล่ออกมาหน้าสุด 🟢 */
        [data-testid="collapsedControl"], [data-testid="stSidebarCollapsedControl"] {{
            visibility: visible !important;
            display: flex !important;
            z-index: 99999 !important;
        }}
        [data-testid="collapsedControl"] svg, [data-testid="stSidebarCollapsedControl"] svg {{
            fill: {text_color} !important;
            color: {text_color} !important;
        }}
        
        /* 5. สไตล์ตัวอักษรและสีพื้นฐาน */
        p, span, label, h1, h2, h3, h4, h5, h6, li, ul, ol, a, strong, b, i, em {{ color: {text_color} !important; }}
        section[data-testid="stSidebar"] {{ background-color: {sidebar_bg} !important; border-right: 1px solid {border_color} !important; }}
        
        /* 6. สไตล์ปุ่มกดต่างๆ */
        [data-testid="stFormSubmitButton"] > button, .stButton > button, [data-testid="stDownloadButton"] > button {{ 
            background-color: #1A73E8 !important; color: #FFFFFF !important; border-radius: 8px !important; border: none !important; 
        }}
        [data-testid="stFormSubmitButton"] p, .stButton p, [data-testid="stDownloadButton"] p {{ color: #FFFFFF !important; }}
        
        /* 7. สไตล์กล่องข้อความและ Input */
        div[data-baseweb="select"] > div, div[data-baseweb="input"] > div, .stTextInput div[data-baseweb="input"] {{ background-color: {input_bg} !important; border: 1px solid {border_color} !important; }}
        div[data-baseweb="select"] span, div[data-baseweb="input"] input, div[data-testid="stChatInput"] textarea {{ color: {input_text} !important; -webkit-text-fill-color: {input_text} !important; }}
        div[data-baseweb="select"] svg {{ fill: {input_text} !important; }}
        [data-testid="stBottom"], [data-testid="stBottom"] > div {{ background: transparent !important; }}
        div[data-testid="stChatInput"] {{ background-color: {input_bg} !important; border: 1px solid {border_color} !important; border-radius: 20px !important; }}

        /* 8. ข้อความต้อนรับและกล่องแชท */
        .greeting-title {{ font-size: 2.8rem; font-weight: 400; color: {text_color}; text-align: center; margin-top: 6rem; margin-bottom: 2rem; font-family: 'Google Sans', sans-serif, Segoe UI; }}
        
        div[data-testid="stChatMessage"]:has([data-testid*="user"]), div[data-testid="stChatMessage"]:has([data-testid*="User"]) {{ flex-direction: row-reverse !important; background-color: {user_bg} !important; margin-left: auto !important; margin-right: 0 !important; border-radius: 20px 20px 4px 20px !important; padding: 1rem 1.5rem !important; max-width: 80% !important; border: none !important; }}
        div[data-testid="stChatMessage"]:has([data-testid*="user"]) [data-testid="stMarkdownContainer"] *, div[data-testid="stChatMessage"]:has([data-testid*="User"]) [data-testid="stMarkdownContainer"] * {{ color: {user_text} !important; }}
        
        div[data-testid="stChatMessage"]:has([data-testid*="assistant"]), div[data-testid="stChatMessage"]:has([data-testid*="Assistant"]) {{ flex-direction: row !important; background-color: {ai_bg} !important; margin-right: auto !important; margin-left: 0 !important; border-radius: 20px 20px 20px 4px !important; padding: 1rem 1.5rem !important; max-width: 80% !important; border: 1px solid {border_color} !important; }}
        div[data-testid="stChatMessage"]:has([data-testid*="assistant"]) [data-testid="stMarkdownContainer"] *, div[data-testid="stChatMessage"]:has([data-testid*="Assistant"]) [data-testid="stMarkdownContainer"] * {{ color: {ai_text} !important; }}
        
        /* 9. กล่องอัปโหลดไฟล์ (File Uploader) */
        [data-testid="stFileUploaderDropzone"] {{
            background-color: {input_bg} !important; border: 1px dashed {border_color} !important;
        }}
        [data-testid="stFileUploaderDropzone"] div, [data-testid="stFileUploaderDropzone"] span, [data-testid="stFileUploaderDropzone"] small, [data-testid="stFileUploaderDropzone"] svg {{
            color: {input_text} !important; fill: {input_text} !important;
        }}
        </style>
    """, unsafe_allow_html=True)
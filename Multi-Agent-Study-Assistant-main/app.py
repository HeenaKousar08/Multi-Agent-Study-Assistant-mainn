import streamlit as st
import os
import json
import hashlib
import subprocess
from datetime import datetime
from dotenv import load_dotenv

# --- 1. INITIALIZATION & API SECURITY ---
load_dotenv()
# Critical: Ensure agents can access the key for Phidata backend
if os.getenv("GROQ_API_KEY"):
    os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

from agent_handler import StudyAssistantHandler
from config import ConfigManager

USER_DB = "users.json"
config_manager = ConfigManager()

# Initialize Session State Defaults
state_defaults = {
    "step": 1, "logged_in": False, "username": "", "active_view": None,
    "chat_history": [], "user_notes": [], "bookmarks": [], "roadmap": "",
    "topic": "", "subject_category": "", "knowledge_level": "",
    "learning_goal": "", "time_available": "", "learning_style": "",
    "current_quiz": None, "quiz_step": 0, "show_feedback": False, "code_output": None
}

for key, value in state_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- 2. AUTHENTICATION ---
def load_users():
    if not os.path.exists(USER_DB):
        with open(USER_DB, "w") as f: json.dump({}, f)
    with open(USER_DB, "r") as f: return json.load(f)

def save_users(users):
    with open(USER_DB, "w") as f: json.dump(users, f, indent=4)

def hash_password(p): return hashlib.sha256(p.encode()).hexdigest()

def login_user(u, p): return load_users().get(u) == hash_password(p)

def register_user(u, p):
    users = load_users()
    if u in users: return False
    users[u] = hash_password(p); save_users(users); return True

# --- 3. UI ENGINE & THEMES ---
st.set_page_config(page_title="Multi-Agent AI Study Assistant", page_icon="📚", layout="wide")

themes = {
    "Corporate Blue": {"primary": "#1e3a8a", "accent": "#3b82f6", "bg": "#f8fafc", "grad": "linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%)"},
    "Dark Professional": {"primary": "#111827", "accent": "#6366f1", "bg": "#111827", "grad": "linear-gradient(135deg, #111827 0%, #374151 100%)"},
    "Royal Purple": {"primary": "#581c87", "accent": "#8b5cf6", "bg": "#f5f3ff", "grad": "linear-gradient(135deg, #581c87 0%, #8b5cf6 100%)"},
    "Sunset Orange": {"primary": "#c2410c", "accent": "#f97316", "bg": "#fff7ed", "grad": "linear-gradient(135deg, #c2410c 0%, #f97316 100%)"}
}

with st.sidebar:
    st.markdown("### 🎨 Professional Themes")
    sel_theme = st.selectbox("Choose Theme:", list(themes.keys()))
    t_style = themes[sel_theme]

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    .stApp {{ background-color: {t_style['bg']}; font-family: 'Inter', sans-serif; }}
    .hero-header {{
        background: {t_style['grad']}; padding: 3rem; border-radius: 20px; color: white; 
        text-align: center; margin-bottom: 2rem; box-shadow: 0 15px 35px rgba(0,0,0,0.1);
    }}
    .module-card {{
        background: white; padding: 1.5rem; border-radius: 15px; border-left: 5px solid {t_style['accent']};
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 1.5rem;
    }}
    .stButton>button {{ background: {t_style['grad']}; color: white; border-radius: 10px; font-weight: 600; width: 100%; }}
    .footer-container {{ text-align: center; padding: 2rem; margin-top: 4rem; border-top: 1px solid #e2e8f0; color: #64748b; }}
    </style>
""", unsafe_allow_html=True)

# --- 4. AUTHENTICATION UI ---
# --- 4. AUTHENTICATION UI (ULTRA-PRO EDITION) ---
if not st.session_state.logged_in:
    # 1. Background and Global Pro Styling
    st.markdown(f"""
        <style>
        /* Target the main background */
        .stApp {{
            background: #f1f5f9; /* Subtle light gray background */
        }}
        
        /* The Glass Card Container */
        div[data-testid="stVerticalBlock"] > div:has(div.login-box) {{
            background: white;
            padding: 4rem;
            border-radius: 30px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.1);
            border: 1px solid #e2e8f0;
        }}

        .login-title {{
            font-size: 2.8rem !important;
            font-weight: 800 !important;
            color: {t_style['primary']};
            margin-bottom: 0px !important;
            padding-bottom: 0px !important;
        }}

        .login-subtitle {{
            color: #64748b;
            font-size: 1.1rem;
            margin-bottom: 2rem !important;
        }}

        /* Make tabs look like a toggle switch */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 24px;
            justify-content: center;
            background-color: transparent;
        }}

        .stTabs [data-baseweb="tab"] {{
            height: 50px;
            white-space: pre-wrap;
            background-color: #f8fafc;
            border-radius: 10px;
            padding: 10px 30px;
            font-weight: 600;
            color: #64748b;
        }}

        .stTabs [aria-selected="true"] {{
            background-color: {t_style['primary']} !important;
            color: white !important;
        }}
        </style>
    """, unsafe_allow_html=True)

    # 2. Layout Structure
    _, col_mid, _ = st.columns([0.6, 1, 0.6])
    
    with col_mid:
        # This div class 'login-box' triggers the CSS rule above
        st.markdown("<div class='login-box'>", unsafe_allow_html=True)
        
        # Professional Icon + Title
        st.markdown(f"<h1 class='login-title'>🤖 Agentic Learning Platform</h1>", unsafe_allow_html=True)
        st.markdown("<p class='login-subtitle'>Intelligent Multi-Agent Workspace</p>", unsafe_allow_html=True)
        
        tab_login, tab_reg = st.tabs(["🔑 Sign In", "📝 Create Account"])
        
        with tab_login:
            st.markdown("<br>", unsafe_allow_html=True)
            u_in = st.text_input("Username", key="l_user", placeholder="e.g. HeenaKousar")
            p_in = st.text_input("Password", type="password", key="l_pass", placeholder="••••••••")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Enter Workspace", use_container_width=True):
                if login_user(u_in, p_in):
                    st.session_state.logged_in = True
                    st.session_state.username = u_in
                    st.rerun()
                else:
                    st.error("Access Denied: Invalid Credentials")
                    
        with tab_reg:
            st.markdown("<br>", unsafe_allow_html=True)
            u_reg = st.text_input("New Username", key="r_user")
            p_reg = st.text_input("New Password", type="password", key="r_pass")
            if st.button("Register Now", use_container_width=True):
                if register_user(u_reg, p_reg):
                    st.success("Registration Successful!")
                else:
                    st.warning("User already exists.")
                    
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()
# --- 5. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown(f"### 👋 Welcome, **{st.session_state.username}**")
    if st.button("🔓 Logout"): st.session_state.logged_in = False; st.rerun()
    st.divider()
    
    st.markdown("### ⚡ Quick Actions")
    if st.button("📊 Progress Dashboard"): st.session_state.active_view = "stats"
    if st.button("📝 Study Notes"): st.session_state.active_view = "notes"
    if st.button("🏠 Home Dashboard"): st.session_state.active_view = None
    
    st.divider()
    st.markdown("### 📚 Learning Modules")
    categories = config_manager.get_all_subject_categories()
    for cat in categories:
        with st.expander(f"📁 {cat.title()}"):
            if st.button(f"Start {cat.title()}", key=f"side_{cat}"):
                st.session_state.subject_category = cat; st.session_state.step = 2; st.session_state.active_view = None; st.rerun()

# --- 6. QUICK ACTION VIEWS ---
if st.session_state.active_view == "stats":
    st.markdown(f"## 📊 {st.session_state.username}'s Progress")
    c1, c2, c3 = st.columns(3)
    c1.metric("Questions Asked", len(st.session_state.chat_history))
    c2.metric("Notes Captured", len(st.session_state.user_notes))
    c3.metric("Current Level", st.session_state.knowledge_level if st.session_state.knowledge_level else "Not Set")
    if st.button("Back to Study"): st.session_state.active_view = None; st.rerun()
    st.stop()

elif st.session_state.active_view == "notes":
    st.markdown("## 📝 My Study Notes")
    note_txt = st.text_area("Jot down something new...")
    if st.button("Save Note") and note_txt:
        st.session_state.user_notes.append({"text": note_txt, "time": str(datetime.now())[:16]})
        st.success("Note Saved!")
    for n in st.session_state.user_notes:
        st.markdown(f"<div class='module-card'><b>{n['time']}</b><br>{n['text']}</div>", unsafe_allow_html=True)
    if st.button("Back to Study"): st.session_state.active_view = None; st.rerun()
    st.stop()

# --- 7. MAIN DASHBOARD WORKFLOW ---
st.markdown("<div class='hero-header'><h1>📚 Multi-Agent AI Study Assistant</h1></div>", unsafe_allow_html=True)

if st.session_state.step == 1:
    st.subheader("Select a Learning Category to Begin:")
    cols = st.columns(3)
    for i, cat in enumerate(categories):
        if cols[i % 3].button(f"🎯 {cat.title()}", key=f"main_{cat}"):
            st.session_state.subject_category = cat; st.session_state.step = 2; st.rerun()

elif st.session_state.step == 2:
    st.markdown(f"<div class='module-card'><h3>Configuration: {st.session_state.subject_category.title()}</h3>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    st.session_state.topic = c1.text_input("What is the specific topic?")
    st.session_state.knowledge_level = c1.selectbox("Your Current Level", config_manager.get_all_knowledge_levels())
    st.session_state.time_available = c2.selectbox("Weekly Dedication", ["Light (1-3 hrs)", "Moderate (5-10 hrs)", "Intensive (20+ hrs)"])
    st.session_state.learning_style = c2.selectbox("Preferred Style", config_manager.get_all_learning_styles())
    st.session_state.learning_goal = st.text_input("What is your end goal?")
    if st.button("🚀 Generate Agent-Led Plan"): st.session_state.step = 3; st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.step == 3:
    with st.spinner("🤖 Specialized Agents are collaborating on your profile..."):
        if "handler" not in st.session_state:
            st.session_state.handler = StudyAssistantHandler(
                topic=st.session_state.topic, 
                subject_category=st.session_state.subject_category,
                knowledge_level=st.session_state.knowledge_level, 
                learning_goal=st.session_state.learning_goal,
                time_available=st.session_state.time_available, 
                learning_style=st.session_state.learning_style, # FIXED: Changed from st.session_style
                model_name="llama-3.3-70b-versatile", 
                provider="groq"
            )
        resp = st.session_state.handler.create_roadmap(st.session_state.handler.analyze_student()['analysis'])
        st.session_state.roadmap = resp.get('roadmap') if isinstance(resp, dict) else resp
        st.session_state.step = 4; st.rerun()

elif st.session_state.step == 4:
    st.markdown(f"<div class='module-card' style='text-align: center; background: {t_style['grad']}; color: white;'><h2>🎯 Master Topic: {st.session_state.topic}</h2></div>", unsafe_allow_html=True)
    
    tabs = st.tabs(["🗺️ Roadmap", "💻 Code Lab", "🤖 Tutor Chat", "📝 Level Test", "📄 Docs RAG"])
    
    with tabs[0]: # ROADMAP
        roadmap_text = str(st.session_state.roadmap)
        phases = roadmap_text.split("###")
        if len(phases) > 1:
            st.info(phases[0].strip())
            for phase in phases[1:]:
                if "Phase" in phase:
                    title = phase.split("\n")[0].strip()
                    with st.expander(f"📍 {title}"): st.markdown(phase.replace(title, "").strip())
        else: st.markdown(f"<div class='module-card'>{roadmap_text}</div>", unsafe_allow_html=True)

    with tabs[1]: # CODE LAB
        code = st.text_area("Python Editor", height=200, value="print('Mentor Ready.')")
        if st.button("▶️ Execute"):
            with open("temp.py", "w") as f: f.write(code)
            res = subprocess.run(["python", "temp.py"], capture_output=True, text=True)
            st.code(res.stdout if res.stdout else res.stderr)

    with tabs[2]: # TUTOR CHAT
        for chat in st.session_state.chat_history:
            with st.chat_message(chat["role"]): st.markdown(chat["content"])
        if prompt := st.chat_input("Ask your Mentor..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            with st.chat_message("assistant"):
                ans = st.session_state.handler.get_tutoring(prompt)
                st.markdown(ans); st.session_state.chat_history.append({"role": "assistant", "content": ans})

    with tabs[3]: # INTERACTIVE LEVEL TEST
        st.subheader(f"📝 {st.session_state.knowledge_level.title()} Assessment")
        if st.button("🎲 Generate My Test"):
            with st.spinner("Agents are designing your assessment..."):
                quiz_data = st.session_state.handler.generate_quiz(difficulty_level=st.session_state.knowledge_level)
                st.session_state.current_quiz = quiz_data.get('quiz')
                st.session_state.quiz_step = 0; st.session_state.show_feedback = False; st.rerun()

        if st.session_state.get("current_quiz"):
            questions = [q.strip() for q in st.session_state.current_quiz.split("Question") if q.strip()]
            cur_idx = st.session_state.quiz_step
            if cur_idx < len(questions):
                st.markdown(f"**Question {cur_idx + 1} of {len(questions)}**")
                parts = questions[cur_idx].split("Correct Answer:")
                st.markdown(f"<div class='module-card'>{parts[0]}</div>", unsafe_allow_html=True)
                ans_in = st.text_input("Your Answer:", key=f"ans_{cur_idx}")
                if st.button("Submit Answer"):
                    st.session_state.show_feedback = True; st.rerun()
                if st.session_state.get("show_feedback"):
                    st.success(f"Correct Answer: {parts[1]}" if len(parts)>1 else "Feedback loading...")
                    if st.button("Next Question ➡️"):
                        st.session_state.quiz_step += 1; st.session_state.show_feedback = False; st.rerun()
            else:
                st.balloons(); st.success("Assessment Complete! Excellent work."); st.session_state.current_quiz = None

    with tabs[4]: # RAG
        up = st.file_uploader("Upload PDF")
        if up:
            if not os.path.exists("temp_docs"): os.makedirs("temp_docs")
            path = os.path.join("temp_docs", up.name)
            with open(path, "wb") as f: f.write(up.getbuffer())
            st.session_state.handler.add_document_to_rag(path, "pdf")
            st.success("Document Indexed!")
        rag_q = st.text_input("Ask about your PDF:")
        if st.button("Search Docs") and rag_q: st.info(st.session_state.handler.query_documents(rag_q))

    st.divider()
    if st.button("🏠 New Learning Journey"): st.session_state.step = 1; st.rerun()

# --- 8. FOOTER ---
st.markdown(f"""
    <div class='footer-container'>
        <p>© 2026 Powered by <b>Heena Kousar</b> | Professional AI Mentor</p>
        <p><small>Multi-Agent Orchestration • Groq Powered • Advanced Analytics</small></p>
    </div>
""", unsafe_allow_html=True)
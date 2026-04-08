import streamlit as st
import requests
import json
import time
import plotly.graph_objects as go
import pandas as pd
from bs4 import BeautifulSoup
from inference import get_fix_command
import streamlit.components.v1 as components
from streamlit_lottie import st_lottie

import os
API_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")
THEME_COLOR = "#8b5cf6" # Vibrant Violet
ACCENT_COLOR = "#06b6d4" # Cyber Cyan


st.set_page_config(
    page_title="A11y-Agent Pro Max",
    page_icon="🤖",
    layout="wide"
)

# --- Advanced Animations CSS ---
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    * {{ font-family: 'Outfit', sans-serif; }}
    
    /* Main Backgrounds */
    .stApp {{
        background-color: #111216;
        color: #e2e8f0;
    }}
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {{
        background-color: #1a1b21 !important;
        border-right: 1px solid #2e2f38;
    }}
    
    [data-testid="stSidebar"] .stSelectbox label, [data-testid="stSidebar"] .stTextInput label {{
        color: #9ca3af;
        font-size: 0.75rem;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        font-weight: 500;
        margin-bottom: 4px;
    }}
    
    .stSelectbox > div > div, .stTextInput > div > div > input {{
        background-color: #25262e !important;
        border: 1px solid #374151 !important;
        border-radius: 10px;
        color: white !important;
    }}
    
    /* Top Logo Topbar simulation */
    .top-brand {{
        display: flex;
        align-items: center;
        gap: 8px;
        color: #8b5cf6;
        font-weight: 600;
        font-size: 1.1rem;
        padding-bottom: 20px;
    }}
    
    /* Avatar and Title Area */
    .avatar-container {{
        display: flex;
        justify-content: center;
        position: relative;
        margin-top: 20px;
        margin-bottom: 15px;
    }}
    .avatar-img {{
        width: 90px;
        height: 90px;
        border-radius: 20px;
        object-fit: cover;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }}
    .avatar-badge {{
        position: absolute;
        bottom: 5px;
        transform: translateX(35px);
        background: #06b6d4;
        width: 24px;
        height: 24px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: black;
        font-size: 12px;
        box-shadow: 0 0 15px rgba(6, 182, 212, 0.6);
        border: 2px solid #111216;
    }}
    
    .main-title {{
        text-align: center;
        font-size: 2.2rem;
        font-weight: 700;
        line-height: 1.2;
        margin-bottom: 8px;
        color: #f8fafc;
    }}
    .sub-title {{
        text-align: center;
        font-size: 0.9rem;
        color: #9ca3af;
        margin-bottom: 40px;
    }}
    
    /* Section Headers */
    .section-header {{
        display: flex;
        align-items: center;
        gap: 12px;
        font-size: 1.4rem;
        font-weight: 600;
        color: white;
        margin-top: 30px;
        margin-bottom: 15px;
    }}
    .section-header span {{
        font-size: 1.6rem;
    }}
    
    /* Requirement Card */
    .req-card {{
        background: rgba(139, 92, 246, 0.05);
        border: 1px solid rgba(139, 92, 246, 0.2);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 25px;
    }}
    .req-label {{
        font-size: 0.7rem;
        color: #a78bfa;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-weight: 700;
        margin-bottom: 8px;
    }}
    .req-text {{
        font-size: 1.1rem;
        font-weight: 500;
        line-height: 1.4;
        color: #f8fafc;
    }}
    
    /* Violation Cards */
    .violation-card {{
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        display: flex;
        gap: 15px;
        align-items: center;
        transition: all 0.2s ease;
        border: 1px solid transparent;
    }}
    .violation-crit {{
        background: rgba(244, 63, 94, 0.1);
        border-color: rgba(244, 63, 94, 0.2);
        color: #fda4af;
    }}
    .violation-warn {{
        background: rgba(245, 158, 11, 0.1);
        border-color: rgba(245, 158, 11, 0.2);
        color: #fcd34d;
    }}
    .violation-info {{
        background: rgba(6, 182, 212, 0.1);
        border-color: rgba(6, 182, 212, 0.2);
        color: #a5f3fc;
    }}
    
    .status-badge {{
        font-size: 0.65rem;
        padding: 2px 8px;
        border-radius: 4px;
        font-weight: 700;
        text-transform: uppercase;
    }}
    
    /* Preview Container */
    .preview-box {{
        background: white;
        border-radius: 16px;
        border: 8px solid #2e2f38;
        box-shadow: 0 20px 50px rgba(0,0,0,0.5);
        overflow: hidden;
    }}
    
    .preview-header {{
        background: #2e2f38;
        padding: 8px 16px;
        display: flex;
        align-items: center;
        gap: 8px;
    }}
    .dot {{ height: 10px; width: 10px; border-radius: 50%; display: inline-block; }}
</style>
""", unsafe_allow_html=True)

def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200: return None
    return r.json()

robot_anim = load_lottieurl("https://assets10.lottiefiles.com/packages/lf20_m6cu96p1.json") # Robot scan

# --- Env & Agent Interaction ---
# --- Session State ---
if 'history' not in st.session_state: st.session_state.history = []
if 'current_obs' not in st.session_state: st.session_state.current_obs = None
if 'session_id' not in st.session_state: st.session_state.session_id = None

# --- Actions ---
def reset_env(task_id):
    try:
        resp = requests.post(f"{API_URL}/reset?task_id={task_id}", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            st.session_state.session_id = data["observation"]["metadata"]["session_id"]
            st.session_state.current_obs = data["observation"]
            st.session_state.history = [{"type": "initial", "html": data["observation"]["html_content"], "score": data["observation"]["accessibility_score"]}]
            return True
    except:
        st.error("Backend offline. Please start uvicorn app:app first.")
    return False

def step_env(action_cmds):
    try:
        resp = requests.post(f"{API_URL}/step?session_id={st.session_state.session_id}", 
                            json={"commands": action_cmds}, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            st.session_state.current_obs = data["observation"]
            st.session_state.history.append({
                "type": "step", "actions": action_cmds, "html": data["observation"]["html_content"], 
                "score": data["observation"]["accessibility_score"]
            })
            return data["done"]
    except Exception as e:
        st.error(f"Action failed: {e}")
    return False

# --- Main ---

def main():
    with st.sidebar:
        st.markdown('<div class="top-brand"><span style="font-size:1.4rem;">((•))</span> A11y-Agent</div>', unsafe_allow_html=True)
        
        task_list = ["easy-alt-text", "adaptive-vision", "adaptive-motor", "dynamic-cognitive"]
        t_id = st.selectbox("SCENARIO", task_list, index=2)
        if st.button("Initialize Environment", use_container_width=True):
            if reset_env(t_id): st.rerun()
        
        st.write("")
        st.markdown("<p style='font-size: 0.75rem; color: #9ca3af; font-weight: 600; letter-spacing: 1px; margin-bottom: 8px;'>🧠 MODEL BRAIN</p>", unsafe_allow_html=True)
        st.markdown('<div class="glass-card" style="padding:10px 16px; margin-bottom: 20px;"><span class="status-dot animate-pulse"></span><span style="font-size:0.85rem">Agent: Active</span></div>', unsafe_allow_html=True)
        
        model = st.selectbox("AGENT MODEL", ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo", "claude-3-opus", "gemini-pro"], index=0)
        api_key = st.text_input("OPENAI API KEY", type="password", placeholder="sk-...")
        
        st.markdown("""
            <div class="glass-card" style="background: rgba(139, 92, 246, 0.1); border-color: rgba(139, 92, 246, 0.2); color: #c4b5fd; font-size: 0.8rem; margin-top:20px;">
                The agent uses parallel RL rewards to optimize DOM structures against WCAG 2.1.
            </div>
        """, unsafe_allow_html=True)

    # Main Avatar and Title
    import base64
    def get_base64_image(image_path):
        try:
            with open(image_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode()
        except:
            return ""

    avatar_b64 = get_base64_image("ai_avatar.png")
    if avatar_b64:
        st.markdown(f"""
        <div class="avatar-container">
            <img src="data:image/png;base64,{avatar_b64}" class="avatar-img">
            <div class="avatar-badge">✧</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('<div class="main-title">Adaptive A11y-Agent Pro<br>Max</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Autonomous Reinforcement Learning for Ultra-Inclusive Web Design</div>', unsafe_allow_html=True)
    
    if not st.session_state.current_obs:
        st.markdown('<div class="glass-card" style="text-align: center; color: #fbbf24; background: rgba(251, 191, 36, 0.05); border-color: rgba(251, 191, 36, 0.2);">Please select a scenario from the sidebar to begin building.</div>', unsafe_allow_html=True)
        return

    obs = st.session_state.current_obs
    profile = obs["metadata"].get("profile", "general")
    task_desc = obs["metadata"].get("task_desc", "Optimize accessibility.")
    score = obs["accessibility_score"]

    if score >= 1.0:
        st.balloons()
    
    # Gauge Chart for Health
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = score * 100,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "WCAG Health Index", 'font': {'size': 18, 'color': "white"}},
        delta = {'reference': (st.session_state.history[0]['score'] * 100) if len(st.session_state.history) > 0 else 0, 'increasing': {'color': "#22c55e"}},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "white"},
            'bar': {'color': "#8b5cf6"},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 2,
            'bordercolor': "#374151",
            'steps': [
                {'range': [0, 50], 'color': 'rgba(244, 63, 94, 0.1)'},
                {'range': [50, 85], 'color': 'rgba(245, 158, 11, 0.1)'},
                {'range': [85, 100], 'color': 'rgba(34, 197, 94, 0.1)'}
            ],
            'threshold': {
                'line': {'color': "#06b6d4", 'width': 4},
                'thickness': 0.75,
                'value': 99
            }
        }
    ))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font={'color': "white", 'family': "Outfit"}, height=250, margin=dict(t=50, b=20, l=20, r=20))
    st.plotly_chart(fig, use_container_width=True)
    
    c1, spacer, c2 = st.columns([1, 0.1, 1.2])
    
    with c1:
        st.markdown(f'<div class="section-header"><span style="color:#f97316;">🎯</span> Target: {profile.replace("_", " ").title()}</div>', unsafe_allow_html=True)
        st.markdown(f"""
            <div class="req-card">
                <div class="req-label">SYSTEM GOAL / USER PROFILE</div>
                <div class="req-text">{task_desc}</div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="section-header"><span style="color:#f43f5e;">⚡</span> Real-time Violations</div>', unsafe_allow_html=True)
        
        if not obs["identified_issues"]:
            st.markdown("""
                <div class="violation-card" style="background: rgba(34, 197, 94, 0.1); border-color: rgba(34, 197, 94, 0.2); color: #86efac;">
                    <span style="font-size: 1.5rem;">🎉</span>
                    <div>
                        <div style="font-weight: 700;">UNIVERSAL ACCESSIBILITY ACHIEVED</div>
                        <div style="font-size: 0.8rem; opacity: 0.8;">The DOM structure represents gold-standard WCAG 2.1 mapping.</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        else:
            for issue in obs["identified_issues"]:
                # Parse issue level
                level = "crit" if "Crit" in issue else "warn" if "Warn" in issue or "Violation" in issue else "info"
                css_class = f"violation-{level}"
                badge_text = level.upper()
                
                parts = issue.split(":", 1)
                issue_text = parts[1].strip() if len(parts)>1 else issue
                
                st.markdown(f"""
                <div class="violation-card {css_class}">
                    <div class="status-badge" style="background: currentColor; color: #111;">{badge_text}</div>
                    <div style="font-size: 0.9rem; font-weight: 500;">{issue_text}</div>
                </div>
                """, unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="section-header"><span style="color:#06b6d4;">🌐</span> Live Evolution Preview</div>', unsafe_allow_html=True)
        # Render the HTML in a safe iframe with new preview styling
        with st.container():
            st.markdown("""
                <div class="preview-box">
                    <div class="preview-header">
                        <span class="dot" style="background:#ff5f56;"></span>
                        <span class="dot" style="background:#ffbd2e;"></span>
                        <span class="dot" style="background:#27c93f;"></span>
                        <span style="color:#9ca3af; font-size:0.7rem; margin-left:10px; font-weight:600;">AGENTIC_PREVIEW_v4.0</span>
                    </div>
            """, unsafe_allow_html=True)

            preview_html = f"<style>body{{font-family:'Outfit',sans-serif; padding:20px; background:white; color:#111; border-radius:4px;}} img{{max-width:100%; border:1px dashed #ccc; padding:4px;}} landmark{{ border: 1px solid #ddd; padding: 4px; display: block; margin: 4px 0; }}</style>{obs['html_content']}"
            components.html(preview_html, height=450, scrolling=True)
            
            # Overlay HUD branding
            st.markdown("""
                    <div style="background:#1a1b21; padding:16px; border-top:1px solid #374151; display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <div style="color:#9ca3af; font-size:0.6rem; letter-spacing:2px; margin-bottom:2px;">NEURAL_MAPPING_SEQUENCE</div>
                            <div style="color:white; font-size:0.8rem; font-weight:700;">LIVE_DOM_EVOLUTION</div>
                        </div>
                        <div style="background:rgba(6,182,212,0.1); color:#06b6d4; padding:4px 10px; border-radius:6px; font-size:0.7rem; font-weight:700; border:1px solid rgba(6,182,212,0.3);">
                            SYNC_ACTIVE
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)


        st.write("")
        if st.button("⚡ Trigger Fix Engine", use_container_width=True):
            with st.spinner("Reconstructing DOM logic..."):
                cmds = get_fix_command(obs["html_content"], obs["identified_issues"], model_name=model, api_key=api_key, custom_prompt=profile)
                if cmds:
                    step_env(cmds)
                    time.sleep(0.5)
                    st.rerun()

    st.markdown("<br><hr style='border-color:#2e2f38;'><br>", unsafe_allow_html=True)
    t1, t2, t3, t4 = st.tabs(["📈 Performance Progress", "📄 Source Diff", "📜 Action Log", "🛠️ Manual Batch"])
            
    with t1:
        if len(st.session_state.history) > 1:
            df = pd.DataFrame([{"Step": i, "Score": h["score"]} for i, h in enumerate(st.session_state.history)])
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df.Step, y=df.Score, mode='lines+markers', name='Health Index', line=dict(color="#06b6d4", width=3)))
            fig.update_layout(title="Agent Rectification Progression", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white", height=300)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Trigger the Fix Engine to see performance progression here.")

    with t2:
        source_col1, source_col2 = st.columns(2)
        source_col1.markdown("#### Original")
        source_col1.code(st.session_state.history[0]["html"], language="html")
        source_col2.markdown("#### Optimized")
        source_col2.code(obs["html_content"], language="html")

    with t3:
        for i, h in enumerate(st.session_state.history[1:]):
            acts = ", ".join(h['actions']) if isinstance(h['actions'], list) else h['actions']
            st.markdown(f"**Turn {i+1}:** Applied `{acts}` → Health: `{int(h['score']*100)}%`")

    with t4:
        manual_cmds = st.text_area("Input Commands (one per line)", placeholder='wrap_element(".nav", "nav")')
        if st.button("Execute Batch"):
            clean_cmds = [c.strip() for c in manual_cmds.split("\n") if c.strip()]
            if clean_cmds:
                step_env(clean_cmds)
                st.rerun()


    # Footer
    st.markdown("""
        <div style="text-align:center; padding: 40px 0 20px 0; color:#6b7280; font-size:0.7rem; letter-spacing: 1px;">
            © 2024 ADAPTIVE A11Y INTELLIGENCE • NEURAL IMPLANT ENABLED
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

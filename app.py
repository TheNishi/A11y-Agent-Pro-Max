from fastapi import FastAPI, HTTPException, Body
from models import Observation, Action, StepResponse, ResetResponse, StateResponse
from environment import A11yEnvironment, UserProfile
import uuid

app = FastAPI(title="A11y-Env: Adaptive Web Accessibility Hub")

# In-memory store for sessions (task instance per agent)
sessions = {}

# Expanded TASKS with more complex scenarios
TASKS = {
    "easy-alt-text": {
        "html": '<html><body><img id="logo" src="logo.png"><h1>Welcome</h1></body></html>',
        "desc": "The page is missing a language attribute and the logo needs alt text.",
        "profile": UserProfile.GENERAL
    },
    "adaptive-vision": {
        "html": '''<html lang="en"><body>
            <div class="header">
                <img src="logo.png" id="main-logo">
                <span>Company Name</span>
            </div>
            <div class="nav">
                <a href="/about">About</a> <a href="/contact">Contact</a>
            </div>
            <img src="hero-banner.jpg" id="hero">
            <h3>Our Mission</h3>
            <p>We make things accessible.</p>
            <button id="cta-btn">Learn More</button>
        </body></html>''',
        "desc": "Adapt this high-level structure for a Vision Impaired user. Convert divs to landmarks and add ARIA/Alt text.",
        "profile": UserProfile.VISION_IMPAIRED
    },
    "adaptive-motor": {
        "html": '''<html lang="en"><body>
            <h1>Sign Up</h1>
            <div class="form-group">
                <span>Username:</span> <input type="text" id="user-input">
            </div>
            <div class="form-group">
                <span>Email:</span> <input type="email" id="email-input">
            </div>
            <div id="submit-button" onclick="submit()">Submit Application</div>
        </body></html>''',
        "desc": "Fix form accessibility for Motor Impaired users. Ensure proper labels and convert the fake button to a real button.",
        "profile": UserProfile.MOTOR_IMPAIRED
    },
    "dynamic-cognitive": {
        "html": '''<html lang="en"><body>
            <div id="header">Header</div>
            <main>
                <h1>Information Density</h1>
                <p>Flashy content and complex layouts can be hard to follow.</p>
                <div class="sidebar">Ads and lots of links...</div>
                <div class="content">Core info here...</div>
            </main>
        </body></html>''',
        "desc": "Simplify navigation and structure for Cognitive Impairment. Ensure clarity and standard landmark usage.",
        "profile": UserProfile.COGNITIVE_IMPAIRED
    }
}

@app.post("/reset", response_model=ResetResponse)
async def reset(task_id: str = "easy-alt-text"):
    if task_id not in TASKS:
        task_id = list(TASKS.keys())[0]
    
    task_cfg = TASKS[task_id]
    session_id = str(uuid.uuid4())
    env = A11yEnvironment(task_cfg["html"], task_id, profile=task_cfg.get("profile", UserProfile.GENERAL))
    html, score, issues = env.reset()
    
    sessions[session_id] = env
    
    obs = Observation(
        html_content=html,
        accessibility_score=score,
        identified_issues=issues,
        metadata={
            "session_id": session_id, 
            "task_id": task_id,
            "task_desc": task_cfg["desc"], 
            "profile": env.profile.value
        }
    )
    return ResetResponse(observation=obs, info={})

@app.post("/step", response_model=StepResponse)
async def step(session_id: str, action: Action):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found. Did you call /reset?")
    
    env = sessions[session_id]
    html, reward, done, issues = env.step(action.commands)
    
    obs = Observation(
        html_content=html,
        accessibility_score=reward, # In this env, score is our reward signal
        identified_issues=issues,
        metadata={"session_id": session_id, "profile": env.profile.value}
    )
    
    return StepResponse(observation=obs, reward=reward, done=done, info={})

@app.get("/state", response_model=StateResponse)
async def state(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found.")
    
    env = sessions[session_id]
    score, issues = env.compute_score(env.current_html)
    
    obs = Observation(
        html_content=env.current_html,
        accessibility_score=score,
        identified_issues=issues,
        metadata={"session_id": session_id, "profile": env.profile.value}
    )
    return StateResponse(observation=obs, info={})

@app.get("/")
async def root():
    return {"status": "A11y-Env Up", "version": "1.0", "tasks": list(TASKS.keys())}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from models import Observation, Action, StepResponse, ResetResponse, StateResponse, GradeResponse
from environment import A11yEnvironment, UserProfile
from typing import Optional, Dict, Any, List, Tuple
import uuid
import uvicorn
import os

try:
    from openenv.core import Task, TaskSuite, registry
    HAS_OPENENV_SDK = True
except ImportError:
    HAS_OPENENV_SDK = False

app = FastAPI(title="A11y-Env: Adaptive Web Accessibility Hub")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- SDK CONFIGURATION (FOR META DISCOVERY) ---
if HAS_OPENENV_SDK:
    # 1. Define internal tasks to match YAML exactly
    openenv_tasks = [
        Task(id="easy-alt-text", difficulty="easy", description="Fix basic A11y issues."),
        Task(id="vision-aria", difficulty="medium", description="Implement aria-labels."),
        Task(id="motor-labels", difficulty="medium", description="Ensure form input labels."),
        Task(id="cognitive-landmarks", difficulty="hard", description="Use semantic landmarks."),
        Task(id="form-validation", difficulty="hard", description="Advanced ARIA validation."),
    ]

    # Universal Grader signature for any SDK version
    def global_grader(*args, **kwargs):
        # Polymorphic extraction of task_id and state
        task_id = next((a for a in args if isinstance(a, str)), kwargs.get("task_id", ""))
        state = next((a for a in args if not isinstance(a, str)), kwargs.get("state", None))
        
        # HTML derivation
        html = ""
        if isinstance(state, str): html = state
        elif isinstance(state, dict): html = state.get("html_content", state.get("html", ""))
        elif hasattr(state, "html_content"): html = getattr(state, "html_content")
        
        temp_env = A11yEnvironment(html or "<html></html>", task_id or "easy-alt-text")
        score, feedback = temp_env._compute_score_raw(temp_env.current_html)
        return float(score), bool(score >= 0.8), list(feedback)

    # 3. Register under every variant for discovery immunity in MAIN entry
    for ident in ["a11y-env", "a11y-agent-pro-max", "A11y-Agent-Pro-Max"]:
        suite = TaskSuite(id=ident, name=ident, tasks=openenv_tasks, grader=global_grader)
        suite.grader = global_grader # Property injection
        registry.register_suite(suite)
        print(f"[SDK-MAIN] Successfully Registered suite: {ident}")

# --- REST OF THE APP ---
# In-memory store for sessions (task instance per agent)
sessions: Dict[str, A11yEnvironment] = {}

# COMPLIANCE: Standardized 5-Task Suite
TASKS = {
    "easy-alt-text": {
        "html": '<html><body><img id="logo" src="logo.png"><h1>Welcome</h1></body></html>',
        "desc": "The page is missing a language attribute and the logo needs alt text.",
        "profile": UserProfile.GENERAL
    },
    "vision-aria": {
        "html": '<html><body><button id="menu">☰</button></body></html>',
        "desc": "Add an aria-label to the menu button for screen readers.",
        "profile": UserProfile.VISION_IMPAIRED
    },
    "motor-labels": {
        "html": '<html><body><span>Name:</span><input type="text" id="name"></body></html>',
        "desc": "Add a proper <label> for the name input.",
        "profile": UserProfile.MOTOR_IMPAIRED
    },
    "cognitive-landmarks": {
        "html": '<html><body><div id="content">Main Content</div></body></html>',
        "desc": "Wrap content in a <main> landmark.",
        "profile": UserProfile.COGNITIVE_IMPAIRED
    },
    "form-validation": {
        "html": '<html><body><form><input type="text" id="zip"></form></body></html>',
        "desc": "Add aria-required to the zip field.",
        "profile": UserProfile.GENERAL
    }
}

@app.post("/reset", response_model=ResetResponse)
async def reset(task_id: Optional[str] = None, body: Dict[str, Any] = Body(default={})):
    # 1. Extract task_id with strict fallback
    final_task_id = task_id or body.get("task_id")
    
    # 2. Strict ID Enforcement: No fuzzy matching which can lead to "missing grader" errors
    if not final_task_id or final_task_id not in TASKS:
        print(f"[ERROR] Task ID '{final_task_id}' not found. Defaulting to 'easy-alt-text'.")
        final_task_id = "easy-alt-text"
    
    task_cfg = TASKS[final_task_id]
    session_id = str(uuid.uuid4())
    env = A11yEnvironment(task_cfg["html"], final_task_id, profile=task_cfg.get("profile", UserProfile.GENERAL))
    
    obs = env.reset()
    obs.metadata["session_id"] = session_id
    obs.metadata["task_desc"] = task_cfg["desc"]
    
    sessions[session_id] = env
    return ResetResponse(observation=obs, info={})

@app.post("/step", response_model=StepResponse)
async def step(action: Action, session_id: Optional[str] = None):
    # Flexible session_id extraction (Query or body if supported)
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required as a query parameter.")
    
    if session_id not in sessions:
        print(f"[ERROR] Step failed: Session {session_id} not active.")
        raise HTTPException(status_code=404, detail="Session not found.")
    
    env = sessions[session_id]
    obs = env.step(action)
    obs.metadata["session_id"] = session_id
    
    return StepResponse(
        observation=obs, 
        reward=float(env.last_reward), 
        score=float(obs.accessibility_score),
        done=bool(env.is_done), 
        info={}
    )

@app.api_route("/state", methods=["GET", "POST"], response_model=StateResponse)
async def state(session_id: Optional[str] = None, body: Dict[str, Any] = Body(default={})):
    actual_session_id = session_id or body.get("session_id")
    if not actual_session_id or actual_session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found.")
    
    env = sessions[actual_session_id]
    current_state = env.state
    obs = Observation(
        html_content=current_state.html_content,
        accessibility_score=current_state.accessibility_score,
        identified_issues=current_state.identified_issues,
        metadata={
            "session_id": actual_session_id,
            "task_id": env.task_id,
            "step": env.steps_taken
        }
    )
    return StateResponse(observation=obs, info={})

@app.api_route("/grade", methods=["GET", "POST"], response_model=GradeResponse)
async def grade(session_id: Optional[str] = None, body: Dict[str, Any] = Body(default={})):
    """Hybrid Grader: Supports both Session-based and Stateless (State-based) evaluation."""
    actual_session_id = session_id or body.get("session_id")
    
    # CASE 1: Session-based (Live agent interaction)
    if actual_session_id in sessions:
        env = sessions[actual_session_id]
        task_id = env.task_id
        html = env.current_html
    
    # CASE 2: Stateless (Validator direct state check)
    elif "task_id" in body and "html" in body:
        task_id = body["task_id"]
        html = body["html"]
        print(f"[AUDIT] Stateless Grade request for task {task_id}")
    
    else:
        print(f"[ERROR] Grade request failed: No session and no state provided.")
        raise HTTPException(status_code=400, detail="Either session_id or (task_id AND html) is required.")

    # Execute Grading Logic
    # Re-using Environment logic for consistency
    temp_env = A11yEnvironment(html, task_id)
    score, issues = temp_env._compute_score_raw(html)
    
    # REQUIREMENT: Boolean solved status and mapped score range
    # 0.8 is a competitive threshold for accessibility
    is_solved = bool(score >= 0.80)
    
    print(f"[AUDIT] Grading Task: {task_id} | Score: {score} | Solved: {is_solved}")
    
    return GradeResponse(
        task_id=str(task_id),
        score=float(score),
        solved=is_solved,
        feedback=list(issues) if issues else ["Check complete: Environment compliant."]
    )

@app.api_route("/tasks", methods=["GET", "POST"])
async def get_tasks():
    """Universal Discovery Endpoint: Supports both String List and Object List formats."""
    task_list = []
    for tid, tcfg in TASKS.items():
        task_list.append({
            "id": tid,
            "name": tcfg.get("name", tid),
            "description": tcfg.get("desc", ""),
            "difficulty": "medium"
        })
    
    return {
        "tasks": list(TASKS.keys()), # Format 1: List of Strings
        "task_details": task_list,    # Format 2: List of Objects
        "count": len(TASKS)
    }

@app.get("/info")
@app.get("/")
async def root():
    return {"status": "A11y-Env Up", "version": "1.3", "tasks": list(TASKS.keys())}

def main():
    # FORCE 8000: Nginx (Gateway) listens on 7860 and proxies to 8000.
    # On HF Spaces, $PORT is often 7860 - we must NOT bind to it directly.
    logger_port = 8000
    print(f"[STARTUP] API Engine starting on port {logger_port}...")
    uvicorn.run(app, host="0.0.0.0", port=logger_port)

if __name__ == "__main__":
    main()

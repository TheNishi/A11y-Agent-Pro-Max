import os
import json
import re
import requests
from typing import List
from openai import OpenAI

def get_fix_command(html: str, issues: list, model_name: str = "gpt-4o", api_key: str = None, custom_prompt: str = "") -> dict:
    """
    Advanced agent that can rectify multiple issues simultaneously.
    Returns a dictionary with 'reasoning' and 'commands'.
    """
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        # Batch fallback for demonstration speed
        issues_str = str(issues).lower()
        commands = []
        if "missing standard landmark" in issues_str: commands.append('wrap_element(".nav", "nav")')
        if "lacks alt text" in issues_str: commands.append('set_attr("#main-logo", "alt", "Company Logo")')
        if "missing <h1>" in issues_str: commands.append('insert_landmark("body", "h1")')
        return {"reasoning": "Fallback rules applied.", "commands": commands if commands else ['set_attr("html", "lang", "en")']}

    try:
        client = OpenAI(api_key=api_key)
        
        prompt = f"""
### ROLE: LEAD ACCESSIBILITY ARCHITECT (TOP 1% WORLDWIDE)
### TASK: SYSTEMATICALLY RESOLVE ALL WCAG 2.1 VIOLATIONS
### USER PROFILE: {custom_prompt.upper()}

HTML SOURCE:
{html}

VIOLATIONS TO RESOLVE:
{chr(10).join(issues)}

### AVAILABLE COMMANDS:
1. `set_attr(selector, attr, val)` - Set attribute (e.g., lang, alt, aria-label)
2. `change_tag(selector, next_tag)` - Change tag type (e.g., div to nav)
3. `add_aria(selector, type, val)` - Add aria-{{type}} attribute
4. `wrap_element(selector, tag)` - Wrap element in a new tag
5. `remove_element(selector)` - Remove redundant/harmful elements
6. `insert_landmark(parent_selector, tag_name)` - Insert a semantic landmark (header, main, footer, etc.)

### REQUIREMENT:
Analyze the HTML and the issues. Plan a single high-impact turn that fixes as many violations as possible.
Return a JSON object:
{{
  "reasoning": "Step-by-step logic for the chosen fixes",
  "commands": ["cmd1", "cmd2", ...]
}}
"""
        response = client.chat.completions.create(
            model=model_name or "gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={ "type": "json_object" }
        )
        return json.loads(response.choices[0].message.content)
        
    except Exception as e:
        return {"reasoning": f"Error: {e}", "commands": []}

def run_inference(task_id: str = "adaptive-vision", env_url="http://127.0.0.1:8000"):
    """
    OpenEnv Standardized Inference Loop.
    Outputs required [START], [STEP], [END] blocks for validation.
    """
    # Required for validator parsing
    print(f"[START] {task_id}")
    
    try:
        # 1. Reset Environment
        resp = requests.post(f"{env_url}/reset?task_id={task_id}")
        data = resp.json()["observation"]
        session_id = data["metadata"]["session_id"]
        profile = data["metadata"].get("profile", "general")
        initial_score = data["accessibility_score"]
        
        step_count = 0
        done = False
        current_score = initial_score
        
        while not done and step_count < 5:
            step_count += 1
            
            # Get issues from current observation
            issues = data.get("identified_issues", [])
            html = data.get("html_content", "")
            
            if not issues:
                break
                
            # Agent logic
            plan = get_fix_command(html, issues, custom_prompt=profile)
            cmds = plan.get("commands", [])
            reasoning = plan.get("reasoning", "No reasoning provided.")
            
            if not cmds:
                break

            # Execute Step
            step_resp = requests.post(f"{env_url}/step?session_id={session_id}", json={"commands": cmds})
            step_result = step_resp.json()
            
            data = step_result["observation"]
            reward = step_result.get("reward", 0)
            done = step_result.get("done", False)
            current_score = data["accessibility_score"]

            # Required [STEP] output
            print(f"[STEP] step-{step_count} reward-{reward}")
            
            # Professional Logging (Optional but helpful)
            # print(f"  > Reasoning: {reasoning}")
            # print(f"  > Score: {current_score} (Progress: +{reward})")

        # 3. Final summary
        # print(f"\n[🏁] Task Finished. Final Score: {current_score}")

    except Exception as e:
        print(f"Error during inference: {e}")
    finally:
        # Required for validator parsing
        print("[END]")

if __name__ == "__main__":
    import sys
    # Use environment variables if available
    env_url = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
    task = sys.argv[1] if len(sys.argv) > 1 else "adaptive-vision"
    run_inference(task, env_url=env_url)

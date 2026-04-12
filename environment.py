from enum import Enum
import re
import os
from bs4 import BeautifulSoup
from typing import List, Tuple, Dict, Any, Optional
import json
from models import Observation, Action, State

# Required for Meta OpenEnv Phase 2 discovery
try:
    from openenv.core import Task, TaskSuite, registry
    HAS_OPENENV_SDK = True
except ImportError:
    HAS_OPENENV_SDK = False

class UserProfile(str, Enum):
    GENERAL = "general"
    VISION_IMPAIRED = "vision_impaired"
    MOTOR_IMPAIRED = "motor_impaired"
    COGNITIVE_IMPAIRED = "cognitive_impaired"

class A11yEnvironment:
    """Advanced logic for the Adaptive Accessibility RL Environment with expanded WCAG rules."""
    
    def __init__(self, initial_html: str, task_id: str, profile: UserProfile = UserProfile.GENERAL):
        self.initial_html = initial_html
        self.current_html = initial_html
        # ENSURE CASE INSENSITIVITY FOR VALIDATOR DISCOVERY
        self.task_id = str(task_id).lower().strip()
        self.profile = profile
        self.steps_taken = 0
        self.max_steps = 20 
        self.initial_score, _ = self._compute_score_raw(initial_html)
        self.last_reward = 0.0
        self.is_done = False

    def reset(self) -> Observation:
        """Resets the environment and returns the initial observation."""
        self.current_html = self.initial_html
        self.steps_taken = 0
        self.last_reward = 0.0
        self.is_done = False
        score, issues = self._compute_score_raw(self.current_html)
        
        return Observation(
            html_content=self.current_html,
            accessibility_score=score,
            identified_issues=issues,
            metadata={
                "task_id": self.task_id,
                "profile": self.profile.value
            }
        )

    def step(self, action: Action) -> Observation:
        """Executes one step in the environment and returns the new observation."""
        self.steps_taken += 1
        
        # Apply all commands in the action batch
        for cmd in action.commands:
            self.apply_action(cmd)
        
        new_score, new_issues = self._compute_score_raw(self.current_html)
        
        # Termination condition: uses the 0.9 capped threshold
        self.is_done = (new_score >= 0.89) or (self.steps_taken >= self.max_steps)

        # Reward calculation: normalized progress
        # Since new_score is in [0.1, 0.9], we scale improvement
        if new_score >= 0.89:
            self.last_reward = 0.9
        elif new_score > self.initial_score:
            # Scaled progress improvement, mapped to (0.1, 0.9)
            improvement = (new_score - self.initial_score) / (0.9 - self.initial_score + 1e-6)
            self.last_reward = 0.1 + (improvement * 0.8)
        else:
            self.last_reward = 0.1
        
        return Observation(
            html_content=self.current_html,
            accessibility_score=new_score,
            identified_issues=new_issues,
            metadata={
                "step": self.steps_taken,
                "reward": self.last_reward,
                "done": self.is_done
            }
        )

    @property
    def state(self) -> State:
        """Returns the current state of the environment."""
        score, issues = self._compute_score_raw(self.current_html)
        return State(
            html_content=self.current_html,
            accessibility_score=score,
            identified_issues=issues,
            metadata={
                "task_id": self.task_id,
                "profile": self.profile.value
            },
            steps_taken=self.steps_taken
        )

    def apply_action(self, cmd: str):
        """Parses and applies complex DOM modifications."""
        soup = BeautifulSoup(self.current_html, "html.parser")
        cmd = cmd.strip()
        
        try:
            if cmd.startswith("set_attr"):
                m = re.search(r"set_attr\s*\(\s*['\"](.+?)['\"]\s*,\s*['\"](.+?)['\"]\s*,\s*['\"](.+?)['\"]\s*\)", cmd)
                if m:
                    selector, attr, val = m.groups()
                    el = soup.find("html") if selector.lower() == "html" else soup.select_one(selector)
                    if el: el[attr] = val

            elif cmd.startswith("change_tag"):
                m = re.search(r"change_tag\s*\(\s*['\"](.+?)['\"]\s*,\s*['\"](.+?)['\"]\s*\)", cmd)
                if m:
                    selector, new_tag = m.groups()
                    el = soup.select_one(selector)
                    if el: el.name = new_tag

            elif cmd.startswith("add_aria"):
                m = re.search(r"add_aria\s*\(\s*['\"](.+?)['\"]\s*,\s*['\"](.+?)['\"]\s*,\s*['\"](.+?)['\"]\s*\)", cmd)
                if m:
                    selector, aria_type, val = m.groups()
                    el = soup.select_one(selector)
                    if el: el[f"aria-{aria_type}"] = val

            elif cmd.startswith("wrap_element"):
                m = re.search(r"wrap_element\s*\(\s*['\"](.+?)['\"]\s*,\s*['\"](.+?)['\"]\s*\)", cmd)
                if m:
                    selector, wrapper_tag = m.groups()
                    el = soup.select_one(selector)
                    if el:
                        wrapper = soup.new_tag(wrapper_tag)
                        el.wrap(wrapper)

            elif cmd.startswith("remove_element"):
                m = re.search(r"remove_element\s*\(\s*['\"](.+?)['\"]\s*\)", cmd)
                if m:
                    selector = m.groups()[0]
                    el = soup.select_one(selector)
                    if el: el.decompose()
            
            elif cmd.startswith("insert_landmark"):
                m = re.search(r"insert_landmark\s*\(\s*['\"](.+?)['\"]\s*,\s*['\"](.+?)['\"]\s*\)", cmd)
                if m:
                    parent, tag = m.groups()
                    p_el = soup.select_one(parent)
                    if p_el:
                        new_el = soup.new_tag(tag)
                        p_el.append(new_el)

            self.current_html = soup.prettify()
        except Exception as e:
            print(f"Action Error [{cmd}]: {e}")

    def _compute_score_raw(self, html: str) -> Tuple[float, List[str]]:
        """
        Hardened Auditor for Phase 2.
        Separates graders into named functions for better discoverability and robustness.
        """
        try:
            soup = BeautifulSoup(html, "html.parser")
            issues = []
            
            # 1. Base Scores (Structural Compliance)
            struct_score = self._eval_base_structure(soup, issues)
            content_score = self._eval_base_content(soup, issues)
            nav_score = self._eval_base_navigation(soup, issues)
            inter_score = self._eval_base_interactive(soup, issues)
            
            # 2. Task Specific Grader
            task_score = 1.0 # Default
            if self.task_id == "easy-alt-text":
                task_score = self._grade_easy_alt(soup, issues)
            elif self.task_id == "vision-aria":
                task_score = self._grade_vision(soup, issues)
            elif self.task_id == "motor-labels":
                task_score = self._grade_motor(soup, issues)
            elif self.task_id == "cognitive-landmarks":
                task_score = self._grade_cognitive(soup, issues)
            elif self.task_id == "form-validation":
                task_score = self._grade_form(soup, issues)

            # 3. Weighted Aggregation
            total = (
                (struct_score * 0.15) + 
                (content_score * 0.15) + 
                (nav_score * 0.15) + 
                (inter_score * 0.15) + 
                (task_score * 0.40)
            )

            # 4. Mandatory Clamping and Mapping (0.01 to 0.99)
            # Using 0.01 and 0.99 to be even safer from hard boundaries
            raw_clamped = max(0.00, min(1.00, total))
            final_mapped = 0.01 + (raw_clamped * 0.98)

            return float(round(final_mapped, 4)), list(set(issues))

        except Exception as e:
            print(f"GRADER_CRASH: {e}")
            return 0.5, ["CRITICAL: Internal Grader Fallback Activated."]

    def _eval_base_structure(self, soup, issues) -> float:
        score = 0.0
        html = soup.find("html")
        if html and html.get("lang"): score += 1.0
        else: issues.append("Missing lang attribute")
        return score / 1.0

    def _eval_base_content(self, soup, issues) -> float:
        imgs = soup.find_all("img")
        if not imgs: return 1.0
        passes = sum(1 for i in imgs if i.get("alt") is not None)
        if passes < len(imgs): issues.append("Missing alt text")
        return passes / len(imgs)

    def _eval_base_navigation(self, soup, issues) -> float:
        lms = ["nav", "header", "main", "footer"]
        found = sum(1 for l in lms if soup.find(l) or soup.find(attrs={"role": l}))
        if found == 0: issues.append("No landmarks found")
        return min(1.0, found / 1.0)

    def _eval_base_interactive(self, soup, issues) -> float:
        links = soup.find_all("a")
        if not links: return 1.0
        passes = sum(1 for l in links if l.get("href"))
        return passes / len(links)

    # --- SPECIFIC TASK GRADERS ---
    def _grade_easy_alt(self, soup, issues) -> float:
        return self._eval_base_content(soup, issues)

    def _grade_vision(self, soup, issues) -> float:
        has_aria = any(el.get("aria-label") for el in soup.find_all())
        if not has_aria: issues.append("Missing ARIA labels")
        return 1.0 if has_aria else 0.0

    def _grade_motor(self, soup, issues) -> float:
        has_labels = all(soup.find("label", attrs={"for": i.get("id")}) for i in soup.find_all("input"))
        if not has_labels: issues.append("Unlabeled inputs")
        return 1.0 if has_labels else 0.0

    def _grade_cognitive(self, soup, issues) -> float:
        return 1.0 if soup.find("main") else 0.0

    def _grade_aria_expert(self, soup, issues) -> float:
        has_rel = any(el.get("aria-live") or el.get("role") == "alert" for el in soup.find_all())
        return 1.0 if has_rel else 0.0

    def _grade_form(self, soup, issues) -> float:
        has_req = any(el.get("aria-required") for el in soup.find_all("input"))
        return 1.0 if has_req else 0.0





# --- Meta OpenEnv SDK Registration ---
if HAS_OPENENV_SDK:
    # 1. Define internal tasks to match YAML exactly
    openenv_tasks = [
        Task(id="easy-alt-text", difficulty="easy", description="Fix a webpage missing basic accessibility features like language tags and image alt text."),
        Task(id="vision-aria", difficulty="medium", description="Implement aria-labels for interactive elements that lack text content."),
        Task(id="motor-labels", difficulty="medium", description="Ensure all form inputs have associated labels for easier targeting and identification."),
        Task(id="cognitive-landmarks", difficulty="hard", description="Use semantic landmarks to simplify page structure for users with cognitive impairments."),
        Task(id="form-validation", difficulty="hard", description="Enhance form accessibility using advanced ARIA validation states and required flags."),
    ]

    # 2. Define the Grader interface for the SDK
    def global_grader(*args, **kwargs) -> Tuple[float, bool, List[str]]:
        """Universal Grader with robust signature detection (task_id, state vs state, task_id)."""
        try:
            # Detect arguments regardless of order
            task_id = ""
            state = None
            for arg in args:
                if isinstance(arg, str): task_id = arg
                else: state = arg
            
            # Fallback for kwargs
            task_id = kwargs.get("task_id", task_id)
            state = kwargs.get("state", state)

            # Polymorphic HTML extraction
            html = ""
            if isinstance(state, str): html = state
            elif isinstance(state, dict): html = state.get("html_content", state.get("html", ""))
            elif hasattr(state, "html_content"): html = getattr(state, "html_content")
            
            if not html: return 0.5, False, ["Empty state"]

            env = A11yEnvironment(html, task_id)
            score, feedback = env._compute_score_raw(html)
            is_solved = bool(score >= 0.80)
            return float(score), is_solved, list(feedback)
        except Exception as e:
            return 0.5, False, [f"Grader Error: {str(e)}"]

    # 3. Create and Register Suite under EVERY possible identity variant
    identity_variants = ["a11y-env", "a11y-agent-pro-max", "A11y-Agent-Pro-Max"]
    for suite_name in identity_variants:
        suite = TaskSuite(
            id=suite_name,
            name=suite_name, # Match Name to ID exactly
            tasks=openenv_tasks,
            grader=global_grader
        )
        # Double Injection for older SDK compatibility
        suite.grader = global_grader
        registry.register_suite(suite)
        print(f"[SDK-DISCOVERY] Successfully hardened suite: {suite_name}")
    print(f"[SDK] Registered TaskSuite '{suite.id}' with {len(openenv_tasks)} tasks.")

from enum import Enum
import re
from bs4 import BeautifulSoup
from typing import List, Tuple, Dict, Any, Optional
import json

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
        self.task_id = task_id
        self.profile = profile
        self.steps = 0
        self.max_steps = 20 
        self.initial_score, _ = self.compute_score(initial_html)

    def reset(self) -> Tuple[str, float, List[str]]:
        self.current_html = self.initial_html
        self.steps = 0
        score, issues = self.compute_score(self.current_html)
        return self.current_html, score, issues

    def step(self, action_cmds: List[str]) -> Tuple[str, float, bool, List[str]]:
        """Executes a batch of DOM-like modification commands for speed."""
        self.steps += 1
        for cmd in action_cmds:
            self.apply_action(cmd)
        
        new_score, new_issues = self.compute_score(self.current_html)
        reward = new_score - self.initial_score # Progressive reward
        
        # Stop if 100% or max steps
        done = (new_score >= 0.99) or (self.steps >= self.max_steps)
        return self.current_html, new_score, done, new_issues

    def apply_action(self, cmd: str):
        """Parses and applies complex DOM modifications."""
        soup = BeautifulSoup(self.current_html, "html.parser")
        cmd = cmd.strip()
        
        try:
            # Multi-parameter command parsing
            # set_attr(selector, attr, val)
            if cmd.startswith("set_attr"):
                m = re.search(r"set_attr\s*\(\s*['\"](.+?)['\"]\s*,\s*['\"](.+?)['\"]\s*,\s*['\"](.+?)['\"]\s*\)", cmd)
                if m:
                    selector, attr, val = m.groups()
                    el = soup.find("html") if selector.lower() == "html" else soup.select_one(selector)
                    if el: el[attr] = val

            # change_tag(selector, next_tag)
            elif cmd.startswith("change_tag"):
                m = re.search(r"change_tag\s*\(\s*['\"](.+?)['\"]\s*,\s*['\"](.+?)['\"]\s*\)", cmd)
                if m:
                    selector, new_tag = m.groups()
                    el = soup.select_one(selector)
                    if el: el.name = new_tag

            # add_aria(selector, type, val)
            elif cmd.startswith("add_aria"):
                m = re.search(r"add_aria\s*\(\s*['\"](.+?)['\"]\s*,\s*['\"](.+?)['\"]\s*,\s*['\"](.+?)['\"]\s*\)", cmd)
                if m:
                    selector, aria_type, val = m.groups()
                    el = soup.select_one(selector)
                    if el: el[f"aria-{aria_type}"] = val

            # wrap_element(selector, wrapper_tag)
            elif cmd.startswith("wrap_element"):
                m = re.search(r"wrap_element\s*\(\s*['\"](.+?)['\"]\s*,\s*['\"](.+?)['\"]\s*\)", cmd)
                if m:
                    selector, wrapper_tag = m.groups()
                    el = soup.select_one(selector)
                    if el:
                        wrapper = soup.new_tag(wrapper_tag)
                        el.wrap(wrapper)

            # remove_element(selector)
            elif cmd.startswith("remove_element"):
                m = re.search(r"remove_element\s*\(\s*['\"](.+?)['\"]\s*\)", cmd)
                if m:
                    selector = m.groups()[0]
                    el = soup.select_one(selector)
                    if el: el.decompose()
            
            # insert_landmark(parent_selector, tag_name, position='append')
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

    def compute_score(self, html: str) -> Tuple[float, List[str]]:
        """Precision WCAG 2.1 Audit Engine."""
        soup = BeautifulSoup(html, "html.parser")
        issues = []
        
        scores = {
            "structure": {"pass": 0, "total": 0, "weight": 0.2},
            "content": {"pass": 0, "total": 0, "weight": 0.3},
            "navigation": {"pass": 0, "total": 0, "weight": 0.3},
            "interactive": {"pass": 0, "total": 0, "weight": 0.2}
        }

        # Profile Weight Adjustment
        if self.profile == UserProfile.VISION_IMPAIRED:
            scores["content"]["weight"] = 0.5
            scores["navigation"]["weight"] = 0.3
            scores["structure"]["weight"] = 0.1
            scores["interactive"]["weight"] = 0.1
        elif self.profile == UserProfile.MOTOR_IMPAIRED:
            scores["interactive"]["weight"] = 0.5
            scores["navigation"]["weight"] = 0.3
            scores["content"]["weight"] = 0.1
            scores["structure"]["weight"] = 0.1

        # --- 1. Structure (Language & IDs) ---
        scores["structure"]["total"] += 1
        html_tag = soup.find("html")
        if html_tag and html_tag.get("lang"): scores["structure"]["pass"] += 1
        else: issues.append("Crit: <html lang> is missing.")
        
        # Check for Duplicate IDs
        ids = [el["id"] for el in soup.find_all(id=True)]
        scores["structure"]["total"] += 1
        if len(ids) == len(set(ids)): scores["structure"]["pass"] += 1
        else: issues.append("Violation: Duplicate HTML 'id' attributes detected.")

        # --- 2. Headings (Hierarchy) ---
        scores["structure"]["total"] += 1
        headings = [h.name for h in soup.find_all(re.compile("^h[1-6]$"))]
        if "h1" in headings:
            # Check for skipped levels (basic check)
            skipped = False
            for i in range(len(headings)-1):
                curr, nxt = int(headings[i][1]), int(headings[i+1][1])
                if nxt > curr + 1: skipped = True
            
            if not skipped: scores["structure"]["pass"] += 1
            else: issues.append("Warn: Heading levels skipped (e.g., H1 followed by H3).")
        else:
            issues.append("Crit: Page missing <h1>.")

        # --- 3. Content (Images) ---
        images = soup.find_all("img")
        for img in images:
            scores["content"]["total"] += 1
            alt = img.get("alt")
            if alt is not None and (len(alt.strip()) > 0 or img.get("role") == "presentation"):
                scores["content"]["pass"] += 1
            else:
                issues.append(f"Violation: <img> '{img.get('id', 'unnamed')}' lacks alt text or role='presentation'.")

        # --- 4. Navigation (Landmarks) ---
        landmarks = ["header", "main", "footer", "nav", "aside", "section"]
        scores["navigation"]["total"] += 1
        found_landmarks = [lm for lm in landmarks if soup.find(lm) or soup.find(attrs={"role": lm})]
        if len(found_landmarks) >= 3: # Expect at least header, main, footer/nav
            scores["navigation"]["pass"] += 1
        else:
            missing = [l for l in ["header", "main", "footer"] if l not in found_landmarks]
            issues.append(f"Guidance: Missing standard landmarks: {', '.join(missing)}.")

        # --- 5. Interactive (Forms & Buttons) ---
        interactive = soup.find_all(["input", "button", "a", "select", "textarea"])
        for el in interactive:
            scores["interactive"]["total"] += 1
            acc_name = el.get("aria-label") or el.get("aria-labelledby") or el.text.strip()
            
            if el.name == "input" and el.get("id"):
                if soup.find("label", attrs={"for": el.get("id")}): acc_name = True
            
            if acc_name: scores["interactive"]["pass"] += 1
            else: issues.append(f"Crit: Non-accessible interactive element <{el.name}>.")

        # Final Weighted Calculation
        final_score = 0.0
        for cat in scores.values():
            if cat["total"] > 0:
                final_score += (cat["pass"] / cat["total"]) * cat["weight"]
            else:
                final_score += cat["weight"]

        return round(min(1.0, final_score), 2), sorted(list(set(issues)))

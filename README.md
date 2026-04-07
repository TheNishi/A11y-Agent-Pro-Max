---
title: A11y Agent Pro Max
emoji: 🤖
colorFrom: indigo
colorTo: purple
sdk: docker
pinned: false
app_port: 7860
---

# ♿ Adaptive A11y-Env: AI for User-Centered Accessibility

**Adaptive A11y-Env** is a next-generation Reinforcement Learning (RL) environment that trains AI agents to solve web accessibility (A11y) issues dynamically. Unlike static checkers, it implements **Adaptive Web Solving**—optimizing DOM structures for specific user profiles (Vision vs. Motor vs. Cognitive Impairment).

---

## 🚀 Key Advancements
- **🧬 Adaptive User Profiles**: The environment provides a "User Type" context, requiring the agent to prioritize fixes that matter most to that specific disability.
- **⚖️ Weighted Scoring Engine**: Success isn't a flat metric; rewards are dynamically weighted based on the current user's needs (e.g., Vision impaired profile prioritizes ARIA & Alt-text).
- **🤖 Agentic Adaptation**: Real-time integration with LLMs (GPT-4o) to autonomously modify the DOM using specialized commands like `add_aria`.
- **📊 Adaptive Dashboard**: High-fidelity Streamlit UI featuring live "Target Profile" indicators and multi-dimensional health gauges.
- **⚡ Fast-API Engine**: A robust backend that simulates a real developer environment with standard Reset/Step/State RL loops.
- **🐳 Cloud-Ready**: Containerized with a multi-process Docker setup for seamless deployment to Hugging Face Spaces.

---

## 🛠️ Tech Stack
- **Frontend**: Streamlit / Plotly (Visualization)
- **Backend**: FastAPI / Uvicorn (Agent Engine)
- **RL Logic**: Python / BeautifulSoup4 (DOM Manipulation Simulation)
- **AI Brain**: OpenAI API / Hugging Face Inference Endpoints

---

## 📂 Project Structure
```bash
.
├── app.py              # FastAPI Backend (Engine)
├── streamlit_app.py    # Streamlit Frontend (Dashboard)
├── environment.py      # RL Core Logic (WCAG Rules & Scoring)
├── inference.py        # AI Agent (LLM Integration)
├── start.sh            # Multi-process execution script
├── Dockerfile          # Container configuration
├── openenv.yaml        # Competition definition metadata
└── requirements.txt    # Project dependencies
```

---

## 💻 Local Setup & Development

### 1. Installation
Install all required dependencies:
```bash
pip install -r requirements.txt
```

### 2. Running Locally
Launch the integrated backend and frontend:
```bash
# Launch the processes in parallel
./start.sh
```
Alternatively, open two terminals:
- **Terminal 1**: `uvicorn app:app --port 8000`
- **Terminal 2**: `streamlit run streamlit_app.py`

Access the dashboard at `http://localhost:8501`.

---

## 🛰️ Deployment (Hugging Face Spaces)

This project is optimized for Hugging Face Spaces using the **Docker SDK**.

1. Create a new Space on [Hugging Face](https://huggingface.co/new-space).
2. Select the **Docker** SDK.
3. Run the deployment script to prepare your git repository:
   ```bash
   python deploy_to_hf.py
   ```
4. Push your code:
   ```bash
   git remote add space https://huggingface.co/spaces/[YOUR_USERNAME]/[YOUR_SPACE_NAME]
   git push --force space main
   ```

---

## 🏆 Hackathon Submission Details
- **Environment Name**: `a11y-env`
- **Goal**: Achieve a 1.0 (100%) WCAG Health Score using the fewest possible agent steps.
- **Author**: Antigravity Agent (for Scaler-Meta AI)

---

### License
MIT License - Created with ❤️ for advanced accessibility.

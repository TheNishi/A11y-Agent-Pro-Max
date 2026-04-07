import os
import requests
import yaml
import subprocess

def validate():
    print("--- OpenEnv Pre-Submission Validation ---")
    
    # 1. Check Files
    required_files = ["openenv.yaml", "app.py", "inference.py", "Dockerfile", "requirements.txt"]
    for f in required_files:
        if os.path.exists(f):
            print(f"[OK] {f} exists.")
        else:
            print(f"[FAIL] {f} is missing.")

    # 2. Validate YAML
    try:
        with open("openenv.yaml", "r") as f:
            data = yaml.safe_load(f)
            print(f"[OK] openenv.yaml is valid YAML. Env name: {data.get('name')}")
    except Exception as e:
        print(f"[FAIL] openenv.yaml error: {e}")

    # 3. Local Server Check (Optional if running)
    print("\nNOTE: Ensure your FastAPI server is running on port 8000 for full API validation.")
    try:
        resp = requests.post("http://localhost:8000/reset", timeout=2)
        if resp.status_code == 200:
            print("[OK] /reset endpoint responding.")
        else:
            print(f"[WARN] /reset returned {resp.status_code}")
    except:
        print("[SKIP] Local server check (not running).")

    print("\nVALIDATION COMPLETE. Next steps: Build docker and push to HF Spaces.")

if __name__ == "__main__":
    validate()

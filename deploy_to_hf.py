import os
import subprocess

def deploy():
    print("--- 🛰️ Preparing A11y-Env for HF Deployment ---")
    
    # 1. Initialize Git if not already
    if not os.path.exists(".git"):
        subprocess.run(["git", "init"], check=True)
        print("[OK] Git initialized.")

    # 2. Ensure start.sh is executable (required for Linux/Docker)
    if os.path.exists("start.sh"):
        print("[OK] start.sh found.")
        # On Windows, we can't chmod easily, but the Dockerfile has RUN chmod +x

    # 3. Add files
    subprocess.run(["git", "add", "."], check=True)
    print("[OK] Files added to staging.")

    # 4. Commit
    try:
        subprocess.run(["git", "commit", "-m", "Deploying A11y-Env with Dashboard + API"], check=True)
        print("[OK] Changes committed.")
    except:
        print("[SKIP] No changes to commit.")

    print("\n--- 🌐 Next Steps to Generate the Link ---")
    print("1. Create a NEW Space on Hugging Face (https://huggingface.co/new-space).")
    print("2. Set the 'Space SDK' to 'Docker'.")
    print("3. In your current terminal, run these commands:")
    print("   git remote add space https://huggingface.co/spaces/[your-username]/[your-space-name]")
    print("   git push --force space main")
    print("\n--- ✅ Once pushed, your link will be: ---")
    print("   https://huggingface.co/spaces/[your-username]/[your-space-name]")

if __name__ == "__main__":
    deploy()

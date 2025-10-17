import os
import re
from datetime import datetime

# ------------------- Simple Code Generator -------------------
def generate_response(prompt: str) -> str:
    """
    Simulates code generation (replace this with your CLI agent call if available).
    The function saves generated code into app/generated_apps/.
    """
    # Directory where new apps will be stored
    gen_dir = os.path.join(os.path.dirname(__file__), "generated_apps")
    os.makedirs(gen_dir, exist_ok=True)

    # Create a safe file name
    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', prompt.strip().lower())[:25]
    filename = f"{safe_name}.py"
    file_path = os.path.join(gen_dir, filename)

    # Simple generated FastAPI app as example
    code = f"""
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {{"message": "This is an auto-generated app for: {prompt}"}}
"""

    # Save the generated code
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(code)

    print(f"✅ Generated and saved new app: {file_path}")
    return f"Generated and saved new app: {filename} at {datetime.now().isoformat()}"

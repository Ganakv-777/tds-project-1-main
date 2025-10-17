from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
import os
import subprocess

from .llm_generator import generate_response
from .signature import signature
from .github_utils import auth_check as gh_auth_check, create_gist

app = FastAPI(title="AI App Builder", version="2.0.0")


# ------------------- Models -------------------
class TaskIn(BaseModel):
    email: str
    secret: str
    task: str
    round: Optional[int] = 1
    nonce: Optional[str] = None
    brief: Optional[str] = None
    checks: Optional[List[str]] = None
    evaluation_url: Optional[str] = None
    attachments: Optional[List[str]] = None


class TaskResponse(BaseModel):
    task: str
    agent: str = "copilot-cli"
    output: str
    email: str


class GistIn(BaseModel):
    filename: str
    content: str
    description: Optional[str] = "tds-project gist"
    public: Optional[bool] = False


# ------------------- Routes -------------------

@app.get("/")
def home():
    return {"message": "AI App Builder is live. Use /task to describe your app."}


@app.get("/task", response_model=TaskResponse)
def task_get(q: str = Query(..., description="Task description/prompt")):
    out = generate_response(q)
    ident = signature()
    return TaskResponse(task=q, output=out, email=ident["email"])


@app.post("/task", response_model=TaskResponse)
def task_post(body: TaskIn):
    expected = os.getenv("STUDENT_SECRET")
    if expected and body.secret != expected:
        raise HTTPException(status_code=401, detail="invalid secret")

    prompt = body.brief or body.task
    if not prompt:
        raise HTTPException(status_code=400, detail="task/brief is required")

    # 1️⃣ Generate new app code
    out = generate_response(prompt)

    # 2️⃣ Auto push to GitHub to trigger Render redeploy
    try:
        subprocess.run(
            ["git", "add", "."], check=True
        )
        subprocess.run(
            ["git", "commit", "-m", "auto: deploy new app"], check=True
        )
        subprocess.run(
            ["git", "push", "origin", "main"], check=True
        )
        deploy_msg = "✅ Code auto-pushed to GitHub. Render will redeploy shortly."
    except Exception as e:
        deploy_msg = f"⚠️ Git push failed: {e}"

    # 3️⃣ Return response
    email_value = body.email or signature()["email"]
    return TaskResponse(
        task=body.task,
        output=f"{out}\n\n{deploy_msg}",
        email=email_value
    )


# ------------------- GitHub Integration -------------------

@app.get("/github/auth-check")
def github_auth_check():
    return gh_auth_check()


@app.post("/github/gist")
def github_gist(body: GistIn):
    res = create_gist(body.filename, body.content, body.description, body.public or False)
    if not res.get("ok"):
        raise HTTPException(status_code=400, detail=res.get("reason", "failed to create gist"))
    return res

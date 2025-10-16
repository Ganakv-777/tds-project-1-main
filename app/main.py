from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
import os
from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
import os
from .github_utils import auth_check as gh_auth_check, create_gist

from .llm_generator import generate_response
from .signature import signature
from .github_utils import auth_check as gh_auth_check, create_gist

from .llm_generator import generate_response
from .signature import signature

app = FastAPI(title="TDS Project Service", version="1.1.0")

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
    agent: str = "llm"
    output: str
    email: str

"""@app.get("/health")
def health():
    return {"ok": True}"""

# Convenience GET for quick tests
"""@app.get("/task", response_model=TaskResponse, tags=["Receive Task"])
def task_get(q: str = Query(..., description="Task description/prompt")):
    out = generate_response(q)
    ident = signature()
    return TaskResponse(task=q, output=out, email=ident["email"])"""

# Your expected POST /task with body
@app.post("/task", response_model=TaskResponse, tags=["Receive Task"])
def task_post(body: TaskIn):
    expected = os.getenv("STUDENT_SECRET")
    if expected and body.secret != expected:
        raise HTTPException(status_code=401, detail="invalid secret")

    prompt = body.brief or body.task
    if not prompt:
        raise HTTPException(status_code=400, detail="task/brief is required")

    out = generate_response(prompt)
    email_value = body.email or signature()["email"]
    return TaskResponse(task=body.task, output=out, email=email_value)

# Back-compat for your screenshot (/api-endpoint)
@app.post("/api-endpoint")
def api_endpoint(payload: Dict[str, Any]):
    try:
        body = TaskIn(**payload)  # if shape matches TaskIn
        return task_post(body)
    except Exception:
        return {"ok": True, "received": payload}
@app.get("/github/auth-check")
def github_auth_check():
    return gh_auth_check()

class GistIn(BaseModel):
    filename: str
    content: str
    description: Optional[str] = "tds-project gist"
    public: Optional[bool] = False

@app.post("/github/gist")
def github_gist(body: GistIn):
    res = create_gist(body.filename, body.content, body.description, body.public or False)
    if not res.get("ok"):
        raise HTTPException(status_code=400, detail=res.get("reason", "failed to create gist"))
    return res

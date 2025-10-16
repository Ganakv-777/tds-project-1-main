# app/github_utils.py
import os
import httpx

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def auth_check() -> dict:
    """
    Verify the GitHub token by calling the /user endpoint.
    Returns: {"ok": bool, "login": str|None, "scopes": [str], "reason": str|None}
    """
    if not GITHUB_TOKEN:
        return {"ok": False, "login": None, "scopes": [], "reason": "GITHUB_TOKEN not set"}

    url = "https://api.github.com/user"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    try:
        with httpx.Client(timeout=20) as client:
            r = client.get(url, headers=headers)
            scopes_hdr = r.headers.get("X-OAuth-Scopes", "")
            scopes = [s.strip() for s in scopes_hdr.split(",") if s.strip()]
            if r.status_code == 200:
                data = r.json()
                return {"ok": True, "login": data.get("login"), "scopes": scopes, "reason": None}
            return {"ok": False, "login": None, "scopes": scopes, "reason": f"HTTP {r.status_code}: {r.text}"}
    except Exception as e:
        return {"ok": False, "login": None, "scopes": [], "reason": f"{e.__class__.__name__}: {e}"}

def create_gist(filename: str, content: str, description: str = "tds-project gist", public: bool = False) -> dict:
    """
    Create a GitHub Gist if GITHUB_TOKEN is set.
    Returns: {"ok": bool, "url": str|None, "reason": str|None}
    """
    if not GITHUB_TOKEN:
        return {"ok": False, "url": None, "reason": "GITHUB_TOKEN not set"}
    url = "https://api.github.com/gists"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}
    payload = {
        "description": description,
        "public": public,
        "files": {filename: {"content": content}},
    }
    try:
        with httpx.Client(timeout=20) as client:
            r = client.post(url, headers=headers, json=payload)
            if r.status_code in (200, 201):
                data = r.json()
                return {"ok": True, "url": data.get("html_url"), "reason": None}
            return {"ok": False, "url": None, "reason": f"HTTP {r.status_code}: {r.text}"}
    except Exception as e:
        return {"ok": False, "url": None, "reason": f"{e.__class__.__name__}: {e}"}

# app/llm_generator.py
import os
from typing import Optional
from dotenv import load_dotenv, find_dotenv
import httpx

# Load .env safely from the current working dir / project
load_dotenv(find_dotenv(usecwd=True))

# Optional OpenAI SDK path (for fully compatible proxies)
try:
    from openai import OpenAI
except Exception:
    OpenAI = None  # type: ignore

def _get(k: str, default: Optional[str] = None) -> Optional[str]:
    v = os.getenv(k)
    return v if v not in (None, "") else default

def _norm_base(u: Optional[str]) -> Optional[str]:
    return u.rstrip("/") if u else None

def _model() -> str:
    return _get("OPENAI_MODEL", "gpt-4o-mini")  # AiPipe model id if different

def _api_key() -> Optional[str]:
    return _get("OPENAI_API_KEY") or _get("AIPIPE_API_KEY")

def _base_url() -> Optional[str]:
    return _norm_base(_get("OPENAI_BASE_URL") or _get("AIPIPE_BASE_URL"))

def _auth_style() -> Optional[str]:
    # bearer | x-api-key | None (auto-try both)
    v = (_get("AIPIPE_AUTH_STYLE") or "").lower().strip()
    return v if v in ("bearer", "x-api-key") else None

def _sdk_client() -> Optional["OpenAI"]:
    key = _api_key()
    base = _base_url()
    if not key or OpenAI is None:
        return None
    return OpenAI(api_key=key, base_url=base) if base else OpenAI(api_key=key)

def _post_httpx(url: str, headers: dict, payload: dict) -> httpx.Response:
    with httpx.Client(timeout=30) as client:
        return client.post(url, headers=headers, json=payload)

def _chat_url(base: str) -> str:
    # tolerate .../openai/v1 or .../v1 or raw host
    if base.endswith("/openai/v1") or base.endswith("/v1"):
        return f"{base}/chat/completions"
    return f"{base}/v1/chat/completions"

def _try_httpx(model: str, prompt: str) -> str:
    key, base = _api_key(), _base_url()
    if not key or not base:
        return "[MODEL-ERROR] Missing API key or base URL"
    url = _chat_url(base)
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Reply briefly and helpfully."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }

    # Respect explicit auth style if set
    style = _auth_style()
    attempts = []
    if style == "bearer":
        attempts = [{"Authorization": f"Bearer {key}"}]
    elif style == "x-api-key":
        attempts = [{"X-API-Key": key}]
    else:
        attempts = [{"Authorization": f"Bearer {key}"}, {"X-API-Key": key}]

    last_err = None
    for headers in attempts:
        try:
            r = _post_httpx(url, headers, payload)
            if r.status_code == 200:
                data = r.json()
                return (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
            last_err = f"HTTP {r.status_code}: {r.text}"
        except Exception as e:
            last_err = f"{e.__class__.__name__}: {e}"
    return f"[MODEL-ERROR] {last_err or 'Unknown error'} (tried auth styles: " + \
           (style if style else "bearer,x-api-key") + ")"

def generate_response(prompt: str) -> str:
    model = _model()

    # 1) Try OpenAI SDK path (works if proxy is fully compatible)
    client = _sdk_client()
    if client is not None:
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Reply briefly and helpfully."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
            return resp.choices[0].message.content or ""
        except Exception as e:
            # If SDK fails (401 or compatibility), fall through to httpx
            if "401" not in str(e) and "AuthenticationError" not in str(e):
                return f"[MODEL-ERROR] {e.__class__.__name__}: {e}"

    # 2) Fallback: raw HTTP with flexible headers/paths
    out = _try_httpx(model, prompt)
    if out and not out.startswith("[MODEL-ERROR]"):
        return out

    # 3) Final safe fallback (service keeps running)
    return f"[FAKE-MODEL:{model}] Echo: {prompt.strip()[:300]}"

import json
from typing import Optional
from urllib.parse import urlencode, urlparse

from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, Field
from workers import asgi
from js import fetch

UPSTREAM_URL = "https://viscodev.x10.mx/Visco-M1-Flash/api.php"
FACTS_KEY = "facts"

app = FastAPI(
    title="Reckless MS API",
    description="واجهة Reckless MS فوق Visco-M1-Flash، تعمل على Cloudflare Workers.",
    version="1.0.0",
)


def get_env(request: Request):
    # Python Workers expose Cloudflare bindings and secrets through ASGI scope.
    return request.scope["env"]


def require_api_key(request: Request, authorization: Optional[str] = Header(default=None)) -> None:
    secret = getattr(get_env(request), "RECKLESS_MS_API_KEY", None)
    if not secret:
        raise HTTPException(status_code=503, detail="أضف RECKLESS_MS_API_KEY كـ Worker secret أولًا.")
    if authorization != f"Bearer {secret}":
        raise HTTPException(status_code=401, detail="مفتاح API غير صحيح أو غير موجود.")


async def get_facts(request: Request) -> list[str]:
    env = get_env(request)
    try:
        value = await env.FACTS.get(FACTS_KEY)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="تعذر قراءة ذاكرة KV؛ راجع إعداد FACTS binding.") from exc
    if not value:
        return []
    try:
        parsed = json.loads(str(value))
        return parsed if isinstance(parsed, list) else []
    except (TypeError, ValueError):
        return []


def make_profile_prompt(user_text: str, facts: list[str]) -> str:
    knowledge = "\n".join(f"- {fact}" for fact in facts) or "لا توجد معلومات إضافية محفوظة حتى الآن."
    return f"""أنت مساعد دردشة اسمه Reckless MS، ويُعرف أيضًا باسم MS.
المطوّر: @M_S_T_G0
قناة الشركة: https://t.me/MS_mohtal

كن ذكيًا، واضحًا، ودودًا، ومفيدًا. أجب بلغة المستخدم، ولا تدّعِ أنك إنسان أو أنك تتعلم تلقائيًا من المحادثات. إذا لم تعرف معلومة فقل ذلك بوضوح. لا تخترع معلومات عن المطوّر أو الشركة.

معلومات أضافها مالك الخدمة لتستخدمها كمعرفة مساعدة:
{knowledge}

رسالة المستخدم:
{user_text}
"""


def validate_image_url(image_url: str) -> None:
    parsed = urlparse(image_url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise HTTPException(status_code=400, detail="رابط الصورة يجب أن يبدأ بـ http:// أو https://")


async def call_visco(params: dict) -> dict:
    url = f"{UPSTREAM_URL}?{urlencode(params)}"
    try:
        response = await fetch(url)
        body = await response.text()
    except Exception as exc:
        raise HTTPException(status_code=502, detail="تعذر الاتصال بخدمة Visco.") from exc
    if not response.ok:
        raise HTTPException(status_code=502, detail=f"خدمة Visco أعادت HTTP {response.status}.")
    content_type = response.headers.get("content-type") or ""
    if "json" in content_type.lower():
        try:
            return json.loads(str(body))
        except (TypeError, ValueError):
            pass
    return {"response": str(body)}


class ChatRequest(BaseModel):
    text: str = Field(min_length=1, max_length=12000, description="رسالة المستخدم")


class ImageRequest(BaseModel):
    url: str = Field(min_length=8, max_length=2048, description="رابط صورة متاح لخدمة Visco")
    prompt: str = Field(default="ماذا ترى في الصورة؟", min_length=1, max_length=4000)


class LearnRequest(BaseModel):
    fact: str = Field(min_length=2, max_length=2000, description="معلومة تريد حفظها")


@app.get("/")
def root():
    return {
        "name": "Reckless MS",
        "developer": "@M_S_T_G0",
        "company_channel": "https://t.me/MS_mohtal",
        "status": "online",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok", "name": "Reckless MS"}


@app.post("/chat")
async def chat(body: ChatRequest, request: Request, authorization: Optional[str] = Header(default=None)):
    require_api_key(request, authorization)
    prompt = make_profile_prompt(body.text, await get_facts(request))
    return await call_visco({"text": prompt})


@app.post("/image")
async def analyze_image(body: ImageRequest, request: Request, authorization: Optional[str] = Header(default=None)):
    require_api_key(request, authorization)
    validate_image_url(body.url)
    prompt = make_profile_prompt(body.prompt, await get_facts(request))
    return await call_visco({"url": body.url, "prompt": prompt})


@app.post("/learn")
async def learn(body: LearnRequest, request: Request, authorization: Optional[str] = Header(default=None)):
    require_api_key(request, authorization)
    fact = " ".join(body.fact.split())
    env = get_env(request)
    facts = await get_facts(request)
    if fact not in facts:
        facts.append(fact)
    try:
        await env.FACTS.put(FACTS_KEY, json.dumps(facts, ensure_ascii=False))
    except Exception as exc:
        raise HTTPException(status_code=503, detail="تعذر حفظ المعلومة في KV.") from exc
    return {"saved": True, "fact": fact, "note": "حُفظت في Cloudflare KV كمعرفة مساعدة، وليست تدريبًا للنموذج."}


@app.get("/knowledge")
async def knowledge(request: Request, authorization: Optional[str] = Header(default=None)):
    require_api_key(request, authorization)
    return {"facts": await get_facts(request)}


Default = asgi.entrypoint(app)

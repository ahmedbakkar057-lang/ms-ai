from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI(title="Reckless MS API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====== هنا تحدد الاسم والشخصية ======
SYSTEM_PROMPT = """
أنت اسمك "Reckless MS" (أو اختصاراً "MS").
أنت مساعد ذكي جداً، سريع التعلم، وردودك دقيقة ومفيدة.
معلومات ثابتة عنك:
- اسمك: Reckless MS
- مطورك: @M_S_T_G0
- قناة الشركة: https://t.me/MS_mohtal
- بتشتغل على موديل: Visco-M1-Flash
قواعد الرد: رد بنفس لغة المستخدم، كن ودوداً وذكياً.
"""

UPSTREAM = "https://viscodev.x10.mx/Visco-M1-Flash/api.php"

def build_prompt(user_text: str) -> str:
    return f"{SYSTEM_PROMPT.strip()}\n\nUser: {user_text}\nAssistant:"

@app.get("/chat")
def chat(text: str = Query(...)):
    try:
        r = requests.get(UPSTREAM, params={"text": build_prompt(text)}, timeout=60)
        return {"ok": True, "reply": r.text, "model": "Reckless MS"}
    except Exception as e:
        raise HTTPException(500, str(e))
# Reckless MS API — مشروع Cloudflare مسطّح

كل ملفات النشر المطلوبة موجودة في جذر المشروع، ولا يوجد مجلد `src/`:

```text
main.py
pyproject.toml
wrangler.jsonc
README.md
```

## رفع الملفات إلى GitHub من الهاتف أو المتصفح

1. أنشئ مستودعًا جديدًا أو افتح مستودعك الحالي.
2. اختر **Add file → Upload files**.
3. ارفع الملفات الأربعة المذكورة أعلاه إلى جذر المستودع. لا ترفع مجلدًا، ولا ترفع ZIP على أنه بديل عن الملفات المستخرجة.
4. احفظ التغييرات بـ **Commit changes**.

## قبل النشر على Cloudflare

1. أنشئ KV namespace باسم `FACTS` في Cloudflare، وخذ معرّفه.
2. عدّل `wrangler.jsonc` واستبدل `REPLACE_WITH_KV_NAMESPACE_ID` بمعرّف namespace الحقيقي.
3. أضف سرّ حماية الـAPI من الطرفية:

```bash
uv run pywrangler secret put RECKLESS_MS_API_KEY
```

4. من مجلد المشروع، سجّل الدخول وانشره:

```bash
uv run pywrangler deploy
```

يفترض وجود `uv` وPython 3.13 أو أحدث في جهاز النشر. هذا مشروع **Cloudflare Workers**؛ رفع الملفات إلى GitHub وحده لا ينشر API تلقائيًا. اتبع إعدادات Cloudflare Workers لبناء المستودع، أو نفّذ أمر النشر السابق.

بعد النشر تحصل على رابط `workers.dev`. استخدم `/docs` للتجربة، و`POST /chat` للمحادثة، و`POST /image` لتحليل صورة برابط عام.

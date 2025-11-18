from flask import Flask, request, jsonify, render_template
import os
import re
from google import genai

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['JSON_AS_ASCII'] = False
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    app.logger.warning("GEMINI_API_KEY не найден! Убедись, что в Railway Project → Variables есть GEMINI_API_KEY")
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
MODEL_NAME = GEMINI_MODEL
SECURITY_PROMPT = (
    "Ты эксперт по информационной безопасности. Отвечай строго на русском языке.\n"
    "Если вопрос НЕ относится к информационной безопасности, ответь ровно строкой: НЕ ИБ\n"
    "Если относится,то строго ответь так:\n"
    "ИБ:\n"
    "Кратко: <1-2 предложения о сути угрозы>\n"
    "Угроза: <нормализованное название угрозы>\n"
    "Контроли: пункт1; пункт2; пункт3\n"
    "Категории: административные=...; технические=...; физические=...\n"
    "Рекомендации: пункт1; пункт2\n"
    "Стандарты: ISO 27001 A.5.1; НПД 152-ФЗ\n"
    "Не добавляй ничего вне этих строк."
)


def _split_items(value: str) -> list[str]:
    return [part.strip() for part in re.split(r"[;,]", value) if part.strip()]


def _parse_categories(value: str) -> dict:
    categories = {}
    for chunk in value.split(';'):
        name, sep, vals = chunk.partition('=')
        if not sep:
            continue
        items = _split_items(vals)
        if items:
            categories[name.strip()] = items
    return categories


def _parse_ib_answer(text: str) -> dict | None:
    data = {
        "is_security": True,
        "summary": "",
        "normalized_threat": "",
        "controls": [],
        "control_categories": {},
        "recommendations": [],
        "standards": []
    }
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines:
        lower = line.lower()
        if lower.startswith('иб'):
            continue
        key, sep, value = line.partition(':')
        if not sep:
            continue
        key = key.strip().lower()
        value = value.strip()
        if key == 'кратко':
            data['summary'] = value
        elif key == 'угроза':
            data['normalized_threat'] = value
        elif key == 'контроли':
            data['controls'] = _split_items(value)
        elif key == 'категории':
            data['control_categories'] = _parse_categories(value)
        elif key == 'рекомендации':
            data['recommendations'] = _split_items(value)
        elif key == 'стандарты':
            data['standards'] = _split_items(value)
    if any([
        data['summary'],
        data['normalized_threat'],
        data['controls'],
        data['control_categories'],
        data['recommendations'],
        data['standards']
    ]):
        return data
    return None

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
    return response

def _call_model(user_text: str):
    if not _client:
        return {}, True
    try:
        prompt = f"{SECURITY_PROMPT}\n\nПользовательский запрос: {user_text}"
        resp = _client.models.generate_content(
            model=MODEL_NAME,
            contents=[{"role": "user", "parts": [{"text": prompt}]}]
        )
        candidates = getattr(resp, "candidates", None) or []
        if candidates:
            content = getattr(candidates[0], "content", None)
            parts = getattr(content, "parts", None) or []
            if parts:
                text = getattr(parts[0], "text", "").strip()
                if text:
                    upper = text.upper()
                    if upper.startswith("НЕ ИБ"):
                        return {
                            "is_security": False,
                            "response": "Отвечаю только на вопросы по информационной безопасности."
                        }, False
                    parsed = _parse_ib_answer(text)
                    if parsed:
                        return parsed, False
                    app.logger.warning("Gemini ответ вне ожидаемого формата: %s", text)
                    return {"response": text}, False
    except Exception as exc:
        app.logger.exception("Gemini call failed: %s", exc)
    return {}, True

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/assistant', methods=['POST', 'OPTIONS'])
def assistant_api():
    if request.method == 'OPTIONS':
        return ("", 204)
    data = request.get_json(silent=True) or {}
    raw = (data.get('query') or '').strip()
    if not raw:
        return jsonify({"response": "Введите вопрос по информационной безопасности."})
    full, model_unavailable = _call_model(raw)
    if model_unavailable:
        return jsonify({"response": "Модель недоступна или ключ не задан.", "model_unavailable": True})
    if full.get('response'):
        return jsonify(full)
    return jsonify({
        "summary": full.get('summary') or "",
        "threat": full.get('normalized_threat') or "",
        "controls": full.get('controls') or [],
        "control_categories": full.get('control_categories') or {},
        "recommendations": full.get('recommendations') or [],
        "standards": full.get('standards') or []
    })

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)
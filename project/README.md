# ИБ Агент (Flask + чистый Frontend)

## Запуск

1. Создайте и активируйте venv (Windows PowerShell):

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Установите зависимости:

   ```bash
   python -m pip install --upgrade pip
   python -m pip install -r project/requirements.txt
   ```

3. Установите ключ для LLM (Gemini):

   ```powershell
   $env:GEMINI_API_KEY="ВАШ_КЛЮЧ"
   ```

4. (Опционально) выберите модель (по умолчанию `gemini-2.0-flash-lite`):

   ```powershell
   $env:GEMINI_MODEL="gemini-2.0-flash-lite"
   ```

5. (Опционально) Установите ключ доступа к API (если хотите ограничить вызовы):

   ```powershell
   $env:API_KEY="ВАШ_СЕРВЕРНЫЙ_КЛЮЧ"
   ```

6. Запуск сервера:

   ```bash
   python project/app.py
   ```

7. Откройте в браузере: `http://127.0.0.1:5000/`

## API

POST `/api/assistant` (или `/api/query`)

Тело запроса:

```json
{ "query": "несанкционированный доступ к CRM" }
```

Ответ (пример):

```json
{
  "threat": "несанкционированный доступ",
  "controls": ["RBAC", "двухфакторная авторизация", "аудит и логирование"],
  "control_categories": {"administrative": ["политики доступа"], "technical": ["RBAC", "2FA"], "physical": []},
  "recommendations": ["Включить MFA", "Настроить роли и права"],
  "standards": ["ISO 27001 A.9", "NIST SP 800-53 AC-2"]
}
```

Если не ИБ или модель недоступна:

```json
{ "response": "Не могу ответить" }
```

или

```json
{ "response": "Не могу ответить", "model_unavailable": true }
```

## Особенности и логика агента

- Ассистент по ИБ работает через Gemini (нужен `GEMINI_API_KEY`)
- На нерелевантные запросы отвечает строго: `Не могу ответить`
- Возвращает структуру: `threat`, `controls`, `control_categories`, `recommendations`, `standards`
- Без ошибок CORS, поддержка русских символов, чистый JS/HTML/CSS
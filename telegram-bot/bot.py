import os
import json
import time
import logging
import urllib.request
import urllib.error
import urllib.parse

# Configuration (Loaded from environment or defaults)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")
PRIMARY_MODEL = "gemini-3.5-flash-lite"
FALLBACK_MODEL = "gemini-3.8-flash"

CUSTOMSER_DIR = r"C:\Users\da\Documents\CustomsER"
FIXFLOW_DIR = r"C:\Users\da\Documents\WorkFlw"
JUPYTER_URL = "https://jupyter.customser.az"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# User state storage
user_modes = {}       # chat_id -> mode ('servicedesk', 'english', 'general', 'jupyter')
user_histories = {}   # chat_id -> list of message history
authorized_user = 8908923139  # Fixed to Nijat's Telegram ID (Admin)

CONTEXT_KNOWLEDGE = f"""
КОРИСТУВАЧ ТА ЙОГО ПРОЄКТИ:
Користувача звати Ніджат. Він працює в IT-підтримці (ServiceDesk) та розвиває власні проєкти:

1. CustomsER (сайт customser.az):
   - Живий сайт митно-брокерських послуг та транзитних декларацій в Азербайджані (CustomsER Brokerage).
   - Технології: HTML5, CSS3, мультиязичність (AZ, RU, EN через data-i18n), хостинг / деплой.

2. 24Fix.us / FixFlow CRM:
   - CRM-система для бізнесу з ремонту побутової техніки в США (Appliance Repair).
   - Технології: FastAPI backend (Python), SQLite/SQLAlchemy, Vite/JavaScript frontend, аутентифікація.

3. Облачний сервер JupyterHub (сайт {JUPYTER_URL}):
   - Корпоративна аналітична лабораторія для роботи з даними, тренінгів та онлайн-зборів.
   - Профілі при запуску:
     * 📊 Data Science: вже встановлені pandas, numpy, matplotlib, seaborn, openpyxl (Excel), requests.
     * 🐍 Чистий Python: легкий minimal-notebook для базового коду.
   - Як користувачам почати роботу:
     1) Відкрити {JUPYTER_URL}.
     2) Ввести логін (виданий адміністратором) та задати пароль при першому вході.
     3) Обрати профіль «Data Science» і натиснути «Start».
   - Гарячі клавіші: Shift+Enter — запустити код у клітинці.
   - Безпека: реєстрація закрита, автоусиплення через 60 хвилин бездіяльності (файли зберігаються на сервері в /home/jovyan/work).
"""

SERVICEDESK_SYSTEM_PROMPT = f"""Ти — персональний асистент та старший колега фахівця 1-ї лінії технічної підтримки (ServiceDesk).
{CONTEXT_KNOWLEDGE}

Твоє завдання — допомагати швидко опрацьовувати тікети, писати коментарі та відповідати на технічні питання.

СТРУКТУРА ВІДПОВІДІ (використовуй HTML теги <b>, <code>):
1. 🔍 <b>Діагностика:</b>
- Коротко суть проблеми.
- 2-3 швидкі кроки перевірки для 1-ї лінії.
2. 💬 <b>Відповідь користувачу:</b>
- Ввічливе звернення, прості зрозумілі кроки.
3. 🛠 <b>Внутрішній коментар (Work Note):</b>
- Лаконічна фіксація для тікета.
"""

ENGLISH_SYSTEM_PROMPT = f"""You are a friendly, professional American English Speaking & Business Coach.
{CONTEXT_KNOWLEDGE}

YOUR ROLE:
- Chat naturally in modern American conversational English.
- Gently correct mistakes: <b>Tip:</b> Natural way to say this: <i>"..."</i>
- Practice realistic dialogues.
"""

JUPYTER_ASSISTANT_PROMPT = f"""Ти — розумний та дружелюбний консультант платформи JupyterHub ({JUPYTER_URL}).
{CONTEXT_KNOWLEDGE}

ТВОЄ ЗАВДАННЯ:
- Допомагати учасникам зборів та студентам працювати на платформі {JUPYTER_URL}.
- Відповідати на питання про Python, Pandas, побудову графіків (Matplotlib/Seaborn), імпорт Excel.
- Пояснювати, як зайти, як користуватися гарячими клавішами (Shift+Enter), як скачати файл.
- Відповідати ввічливо, зрозуміло, з короткими прикладами робочого коду. Використовуй теги <b>, <code>.
"""

GENERAL_SYSTEM_PROMPT = f"""Ти — швидкий персональний помічник Ніджата та консультант з проєктів.
{CONTEXT_KNOWLEDGE}

Відповідай чітко, структуровано та по суті. Використовуй HTML теги <b>, <i>, <code>.
"""

MEETING_ANNOUNCEMENT = (
    "📊 <b>Колеги, вітаємо на аналітичній сесії!</b>\n\n"
    "Для практичної роботи та роботи з даними ми запустили захищену хмарну лабораторію JupyterHub.\n\n"
    f"🌐 <b>Адреса платформи:</b> {JUPYTER_URL}\n\n"
    "🔹 <b>Що вже готове:</b>\n"
    "• Бібліотеки <code>pandas</code>, <code>numpy</code>, <code>matplotlib</code>, <code>seaborn</code>, <code>openpyxl</code> (Excel) вже встановлені.\n"
    "• Робота прямо у браузері з комп'ютера чи телефона.\n"
    "• Персональна ізольована папка для ваших файлів.\n\n"
    "📋 <b>Як увійти за 1 хвилину:</b>\n"
    f"1. Відкрийте посилання: {JUPYTER_URL}\n"
    "2. Введіть призначений логін.\n"
    "3. При першому вході введіть свій особистий пароль.\n"
    "4. Оберіть профіль <b>«📊 Data Science»</b> та натисніть <b>«Start»</b>.\n\n"
    "💡 <i>Виконувати код у зошиті: сполучення клавіш <b>Shift + Enter</b>.</i>\n"
    "Будь-які запитання щодо коду чи платформи можна ставити прямо цьому боту!"
)

JUPYTER_QUICK_CARD = (
    "🚀 <b>Шпаргалка по платформі JupyterHub</b>\n\n"
    f"🔗 <b>Вхід:</b> {JUPYTER_URL}\n\n"
    "⚙️ <b>Профілі при старті:</b>\n"
    "• <b>📊 Data Science</b> — аналітика, Excel, графіки (обрано за замовчуванням).\n"
    "• <b>🐍 Чистий Python</b> — легке мінімальне середовище.\n\n"
    "⌨️ <b>Головні гарячі клавіші:</b>\n"
    "• <code>Shift + Enter</code> — виконати клітинку та перейти далі\n"
    "• <code>Esc + A</code> — додати нову клітинку вище\n"
    "• <code>Esc + B</code> — додати нову клітинку нижче\n"
    "• <code>Esc + D + D</code> — видалити клітинку\n\n"
    "💾 <i>Всі файли зберігаються в хмарі. При простої понад 1 годину сервер автоматично засинає.</i>"
)

def call_gemini(chat_id, user_text, is_admin=False):
    mode = user_modes.get(chat_id, "jupyter" if not is_admin else "servicedesk")
    
    if mode == "english":
        system_instruction = ENGLISH_SYSTEM_PROMPT
    elif mode == "general":
        system_instruction = GENERAL_SYSTEM_PROMPT
    elif mode == "jupyter":
        system_instruction = JUPYTER_ASSISTANT_PROMPT
    else:
        system_instruction = SERVICEDESK_SYSTEM_PROMPT

    history = user_histories.setdefault(chat_id, [])
    history.append({"role": "user", "parts": [{"text": user_text}]})
    
    if len(history) > 10:
        history = history[-10:]
        user_histories[chat_id] = history

    models_to_try = [PRIMARY_MODEL, FALLBACK_MODEL]
    
    for attempt, model_name in enumerate(models_to_try):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
        payload = {
            "systemInstruction": {
                "parts": [{"text": system_instruction}]
            },
            "contents": history,
            "generationConfig": {
                "temperature": 0.5
            }
        }
        
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                res = json.loads(resp.read().decode())
                reply = res["candidates"][0]["content"]["parts"][0]["text"]
                history.append({"role": "model", "parts": [{"text": reply}]})
                return reply
        except urllib.error.HTTPError as e:
            logging.warning(f"Model {model_name} HTTP {e.code}, attempt {attempt+1}")
            if e.code == 503 or e.code == 429:
                time.sleep(1.5)
                continue
            return f"⚠️ Помилка Gemini API ({e.code}): {e.reason}"
        except Exception as e:
            logging.warning(f"Model {model_name} error: {e}")
            time.sleep(1.5)
            continue
            
    return "⚠️ Сервери Gemini тимчасово перевантажені. Спробуйте ще раз за хвилину."

def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        try:
            payload.pop("parse_mode", None)
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as fallback_resp:
                return json.loads(fallback_resp.read().decode())
        except Exception as ex:
            logging.error(f"Telegram send error: {ex}")
    return None

def handle_message(message):
    chat = message.get("chat", {})
    chat_id = chat.get("id")
    chat_type = chat.get("type", "private")
    text = message.get("text", "").strip()

    if not chat_id or not text:
        return

    is_admin = (chat_id == authorized_user)
    
    # Clean bot username from command in groups, e.g. /meeting@mynotepadhub_bot -> /meeting
    cmd = text.split()[0].lower().replace("@mynotepadhub_bot", "")

    # Universal Commands (available for all participants & groups)
    if cmd in ["/meeting", "/announce"]:
        send_telegram_message(chat_id, MEETING_ANNOUNCEMENT)
        return

    if cmd in ["/jupyter", "/hub"]:
        send_telegram_message(chat_id, JUPYTER_QUICK_CARD)
        return

    # User-specific start command
    if cmd == "/start":
        if is_admin:
            user_modes[chat_id] = "servicedesk"
            welcome = (
                "👋 <b>Привіт, Ніджат! Головне меню адміністратора:</b>\n\n"
                "📢 <b>Для зборів та тренінгів:</b>\n"
                "/meeting — надіслати повідомлення-анонс збору з посиланням\n"
                "/jupyter — картка платформи JupyterHub та гарячі клавіші\n\n"
                "🛠 <b>Режими асистента:</b>\n"
                "/sd — ServiceDesk асистент (за замовчуванням)\n"
                "/en — English Speaking Coach\n"
                "/ai — загальний помічник Gemini\n"
                "/projects — статус проєктів (CustomsER, 24Fix, JupyterHub)\n"
                "/clear — очистити контекст діалогу"
            )
            send_telegram_message(chat_id, welcome)
        else:
            user_modes[chat_id] = "jupyter"
            guest_welcome = (
                "👋 <b>Вітаємо в онлайн-асистенті платформи JupyterHub!</b>\n\n"
                f"🌐 <b>Наша платформа:</b> {JUPYTER_URL}\n\n"
                "Я допомагаю розібратися з роботою на платформі:\n"
                "• /meeting — коротке інфо про поточні збори та вхід\n"
                "• /jupyter — посилання та гарячі клавіші\n\n"
                "💡 <i>Ви можете написати мені будь-яке запитання з Python, Pandas чи роботі з таблицями, і я підкажу код!</i>"
            )
            send_telegram_message(chat_id, guest_welcome)
        return

    if cmd == "/help":
        help_msg = (
            "🤖 <b>Команди бота @mynotepadhub_bot:</b>\n\n"
            "/meeting — інформаційне повідомлення для зборів\n"
            "/jupyter — вхід на платформу та гарячі клавіші\n\n"
            "💬 <i>Просто напишіть мені своє запитання щодо аналітики даних або помилки в коді!</i>"
        )
        send_telegram_message(chat_id, help_msg)
        return

    # Admin only commands
    if is_admin:
        if cmd == "/projects":
            customser_exists = os.path.exists(CUSTOMSER_DIR)
            fixflow_exists = os.path.exists(FIXFLOW_DIR)
            msg = (
                "📁 <b>Твої проєкти:</b>\n\n"
                f"1. <b>CustomsER (customser.az)</b>\n"
                f"   • Статус: {'✅ Знайдено' if customser_exists else '❌ Не знайдено'}\n"
                f"   • Опис: Митно-брокерські та транзитні декларації\n\n"
                f"2. <b>24Fix.us / FixFlow CRM</b>\n"
                f"   • Статус: {'✅ Знайдено' if fixflow_exists else '❌ Не знайдено'}\n"
                f"   • Опис: CRM для ремонту техніки (FastAPI + Vite)\n\n"
                f"3. <b>JupyterHub Cloud ({JUPYTER_URL})</b>\n"
                "   • Статус: 🟢 Онлайн на Google Cloud (35.198.118.205)\n"
                "   • Захист: Закрита реєстрація, Cloudflare SSL, Nginx 444, Idle Culler\n"
            )
            send_telegram_message(chat_id, msg)
            return

        if cmd == "/sd":
            user_modes[chat_id] = "servicedesk"
            send_telegram_message(chat_id, "🛠 <b>Режим ServiceDesk активовано.</b> Надсилай проблему або тікет.")
            return

        if cmd == "/en":
            user_modes[chat_id] = "english"
            send_telegram_message(chat_id, "🇺🇸 <b>English Coach activated!</b> Hi Nijat, let's practice!")
            return

        if cmd == "/ai":
            user_modes[chat_id] = "general"
            send_telegram_message(chat_id, "💡 <b>Режим загального помічника активовано.</b>")
            return

        if cmd == "/clear":
            user_histories[chat_id] = []
            send_telegram_message(chat_id, "🧹 <b>Контекст діалогу очищено.</b>")
            return

    # Process question with Gemini AI
    reply = call_gemini(chat_id, text, is_admin=is_admin)
    send_telegram_message(chat_id, reply)

def main():
    logging.info("Starting Telegram Bot listener for @mynotepadhub_bot...")
    offset = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset={offset}&timeout=20"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = json.loads(resp.read().decode())
                if data.get("ok"):
                    for update in data.get("result", []):
                        offset = update["update_id"] + 1
                        if "message" in update:
                            handle_message(update["message"])
        except Exception as e:
            logging.error(f"Error in main loop: {e}")
            time.sleep(3)

if __name__ == "__main__":
    main()

# 🤖 AI-to-AI System Handoff & Technical Blueprint
**Project:** Centralized Corporate Learning Platform & Safe Scripting Sandbox (JupyterHub + Telegram Bot)  
**Host & Domain:** `https://jupyter.customser.az`  
**GCP Compute Instance:** `jupyter-hub-server` (`europe-west3-a`, External IP: `35.198.118.205`)  
**Target User:** Nijat (`admin`, Telegram ID: `8908923139`)  

---

## 1. 📌 TL;DR Summary (За 30 секунд для нового ИИ)
Мы создали и задеплоили корпоративную облачную платформу интерактивного обучения и написания скриптов на базе **JupyterHub 6.1** в Google Cloud.
- **Цель:** Инициатива для руководства компании по запуску безопасной песочницы для курсов программирования и автоматизации рутины сотрудников без установки софта на рабочие ПК.
- **Изоляция:** Каждый пользователь получает персональный Docker-контейнер с лимитами **512 MB RAM / 0.5 CPU**.
- **Профили:** 1) `📊 Data Science` (pre-installed pandas, numpy, matplotlib, seaborn, openpyxl, requests); 2) `🐍 Чистый Python` (minimal-notebook).
- **Безопасность:** Домен через Cloudflare SSL. Порт 8000 закрыт снаружи и привязан к `127.0.0.1`. Nginx настроен с кодом `444` (blackhole) для прямых сканеров по IP.
- **Idle Culler:** Неактивные более 60 минут сессии автоматически останавливаются, освобождая память; файлы сохраняются на диск.
- **Telegram-бот (@mynotepadhub_bot):** Круглосуточная служба `telegram-bot.service` на GCP VM. Имеет Executive-меню с кнопками для публикации анонса на собрании, выдачи логинов сотрудникам и мониторинга платформы.
- **Репозиторий:** Полный Git-репозиторий собран на локальном ПК в `C:\Users\da\OneDrive\Документы\JupyterHub-Server` и готов к пушу на GitHub (`nijat1212/jupyterhub-server`).

---

## 2. 🏗 Инфраструктура и стек

| Компонент | Расположение | Детали конфигурации |
|---|---|---|
| **VM** | GCP `europe-west3-a` | `jupyter-hub-server` (e2-medium, Ubuntu 22.04 LTS, IP: `35.198.118.205`) |
| **Сеть** | GCP Firewall | Правило `allow-jupyterhub` разрешает только `tcp:80, tcp:443`. Порт `8000` закрыт. |
| **DNS / SSL** | Cloudflare | Проксирование `jupyter.customser.az` -> `35.198.118.205`, режим `SSL: Flexible`. |
| **Reverse Proxy** | `/etc/nginx/sites-available/jupyterhub` | Блокировка прямого IP (`return 444`), WebSocket proxy на `127.0.0.1:8000`. |
| **JupyterHub** | `/opt/jupyterhub/` | Docker Compose, образ `jupyterhub-custom:latest` (network host). |
| **Хранилище** | `/opt/jupyterhub/data/{username}` | Смонтировано в контейнер пользователя как `/home/jovyan/work`. |
| **Telegram Bot** | `/opt/telegram-bot/bot.py` | Systemd служба `telegram-bot.service` (автозапуск при ребуте). |

---

## 3. ⚙️ Ключевые файлы и их назначение

### Сервер VM (`jupyter-hub-server`):
1. **`/opt/jupyterhub/jupyterhub_config.py`**:
   - `c.JupyterHub.bind_url = 'http://127.0.0.1:8000'`
   - `c.JupyterHub.authenticator_class = 'firstuseauthenticator.FirstUseAuthenticator'`
   - `c.Authenticator.admin_users = {'admin'}`
   - `c.Authenticator.allow_all = True` *(Включен на время презентации для бесшовного входа)*
   - `c.Spawner.profile_list`: профили Data Science и Clean Python
   - `c.Spawner.mem_limit = '512M'`, `c.Spawner.cpu_limit = 0.5`
   - `c.JupyterHub.services = [idle-culler]`: `--timeout=3600`, `--cull-every=600`
2. **`/opt/jupyterhub/Dockerfile`**:
   - На базе `jupyterhub/jupyterhub:latest`.
   - Установлены: `dockerspawner`, `jupyterhub-firstuseauthenticator`, `bcrypt`, `jupyterhub-idle-culler`.
3. **`/opt/jupyterhub/Dockerfile.datascience`**:
   - На базе `jupyter/minimal-notebook:latest`.
   - Установлены: `pandas`, `numpy`, `matplotlib`, `seaborn`, `openpyxl`, `requests`.
4. **`/opt/telegram-bot/bot.py`**:
   - Бот `@mynotepadhub_bot`. Токен задается через переменную окружения `TELEGRAM_BOT_TOKEN`.
   - Клавиатура: «🌐 Войти в песочницу», «🔑 Мой доступ», «📂 Примеры скриптов», «❓ Как это устроено», «📢 Опубликовать анонс», «📊 Мониторинг платформы».

### Локальный ПК (`C:\Users\da`):
* Папка репозитория: `C:\Users\da\OneDrive\Документы\JupyterHub-Server`
* Содержит: `docker-compose.yml`, `jupyterhub_config.py`, `Dockerfile`, `Dockerfile.datascience`, `nginx/jupyterhub.conf`, `deploy.sh`, `README.md`, `README.txt`, `.gitignore`, `telegram-bot/bot.py`, `AI_HANDOVER.md`.
* Git: ветка `main`, все коммиты созданы, готов к `git remote add origin https://github.com/nijat1212/jupyterhub-server.git`.

---

## 4. 🎭 Сценарий презентации (Контекст для ИИ)
1. **00:00 - 02:00:** Вводная — запуск курсов для сотрудников, проблема сложной локальной установки ПО и страх сломать рабочую сеть.
2. **02:00 - 04:30:** Продукт — централизованная песочница в браузере, микро-контейнеры, нулевой риск для сети (квоты 512M RAM).
3. **04:30 - 05:30:** Интерактивный вылет сообщения в рабочий чат с телефона (через бота или пересылкой) со ссылкой на платформу.
4. **05:30 - 07:30:** Перспективы масштабирования — от скриптов рутины до корпоративного учебного центра.
5. **07:30 - 09:00:** Технические ответы — стек Docker, возможность в любой момент перенести на внутренние серверы компании (on-premise).

---

## 5. 🛡️ Переключение безопасности после презентации
После собрания, когда все участники зарегистрировались:
1. Зайти в `/opt/jupyterhub/jupyterhub_config.py`.
2. Изменить `c.Authenticator.allow_all = True` на `c.Authenticator.allow_all = False`.
3. Выполнить `sudo docker restart jupyterhub`.
*Результат: текущие зарегистрированные пользователи продолжают работать, а новые регистрации из интернета блокируются.*

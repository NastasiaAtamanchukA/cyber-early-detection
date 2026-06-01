# Cyber Early Detection

Учебный full-stack проект: **система раннего обнаружения кибератак на основе ML и анализа логов**.

Стек: **Python, FastAPI, PostgreSQL, scikit-learn, pandas, React, TypeScript, Vite, Docker, Docker Compose, GitHub Actions, pytest**.

## Что обновлено в этой версии

Добавлены доработки для защиты проекта:

- редактирование расписаний сбора событий;
- добавление пользовательских расписаний через UI;
- включение и отключение расписаний без удаления;
- профиль генерации событий `auth`, `web`, `privileged`, `database`, `mixed`;
- более подробные рекомендации по действиям в инцидентах;
- стильные графики на дашборде: donut chart, risk buckets, timeline, bars;
- обновленные API endpoints для `POST/PATCH /api/v1/collectors/schedules`;
- обновленный CI/CD workflow с backend, ML, frontend и Docker build.

## Что внутри

- `backend` — API на FastAPI, прием логов, нормализация, запись в БД, создание алертов и инцидентов;
- `ml_service` — отдельный ML-сервис на FastAPI + IsolationForest;
- `frontend` — веб-интерфейс SOC-аналитика на React/TypeScript/Vite;
- `docker-compose.yml` — запуск всего проекта одной командой;
- `.github/workflows/ci.yml` — CI для тестов и сборки Docker-образов;
- `docs` — проектные документы и диаграммы.

## Быстрый запуск

Экспортируйте файлы с репозитория с помощью команд
git clone https://github.com/NastasiaAtamanchukA/cyber-early-detection.git


Запустите сборку с помощью Docker и Docker Compose.

```bash
cp .env.example .env
docker compose up --build -d
```

После запуска:

- Frontend: <http://localhost:3000>
- Backend API: <http://localhost:8000>
- Swagger: <http://localhost:8000/docs>
- ML service: <http://localhost:8001>

## Проверка здоровья сервисов

```bash
curl http://localhost:8000/api/v1/health
curl http://localhost:8001/health
```

## Добавить тестовые события

Вариант 1 — скриптом:

```bash
bash scripts/seed_demo.sh
```

Вариант 2 — через страницу **Сбор логов** в интерфейсе:

1. Открыть `http://localhost:3000/collectors`.
2. Добавить свое расписание или выбрать существующее.
3. Нажать **Запустить сейчас**.
4. Вернуться на дашборд и проверить графики, события, алерты и инциденты.

## Основные API

- `POST /api/v1/events/ingest` — принять событие;
- `GET /api/v1/events` — список событий;
- `GET /api/v1/alerts` — список алертов;
- `GET /api/v1/incidents` — список инцидентов с рекомендациями;
- `GET /api/v1/dashboard` — данные для дашборда и графиков;
- `GET /api/v1/collectors/schedules` — список расписаний;
- `POST /api/v1/collectors/schedules` — создать расписание;
- `PATCH /api/v1/collectors/schedules/{id}` — изменить расписание;
- `POST /api/v1/collectors/schedules/{id}/run` — запустить расписание.

## Локальный запуск без Docker

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### ML service

```bash
cd ml_service
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Тесты

```bash
cd backend && PYTHONPATH=. python -m pytest -q
cd ../ml_service && PYTHONPATH=. python -m pytest -q
cd ../frontend && npm install && npm run build
```

## Логика обнаружения

1. Backend принимает JSON-лог.
2. Лог нормализуется и превращается в feature vector.
3. Backend отправляет признаки в ML service.
4. ML service считает риск через IsolationForest.
5. Если риск выше порога, backend создает alert.
6. Для high/critical событий создается incident.
7. Frontend показывает события, алерты, инциденты, рекомендации и графики.

## Ограничения прототипа

Это учебный MVP, а не промышленная SIEM/UEBA-система. Для production понадобятся RBAC, HTTPS, real-time очередь, нормальные парсеры Sysmon/auditd/nginx, корреляционные правила, аудит действий пользователей и мониторинг Prometheus/Grafana.

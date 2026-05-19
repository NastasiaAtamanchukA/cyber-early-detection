# Cyber Early Detection

Учебный full-stack проект: **система раннего обнаружения кибератак на основе ML и анализа логов**.

Стек: **Python, FastAPI, PostgreSQL, scikit-learn, pandas, React, TypeScript, Vite, Docker, Docker Compose, GitHub Actions, pytest**.

## Что внутри

- `backend` — API на FastAPI, прием логов, нормализация, запись в БД, создание алертов
- `ml_service` — отдельный ML-сервис на FastAPI + IsolationForest
- `frontend` — веб-интерфейс SOC-аналитика на React
- `docker-compose.yml` — запуск всего проекта одной командой
- `.github/workflows/ci.yml` — CI для тестов и сборки Docker-образов

## Быстрый запуск

Нужны Docker и Docker Compose.

```bash
cp .env.example .env
docker compose up --build -d
```

После запуска:

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- ML service: http://localhost:8001

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

Вариант 2 — вручную:

```bash
curl -X POST http://localhost:8000/api/v1/events/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2026-05-17T12:00:00Z",
    "host": "srv-01",
    "user": "alice",
    "event_type": "login_failed",
    "message": "Failed SSH login for alice from 10.0.0.15",
    "source_name": "ssh-gateway",
    "source_kind": "json",
    "metadata": {"ip": "10.0.0.15", "port": 22}
  }'
```

## Остановить проект

```bash
docker compose down
```

Чтобы удалить данные БД и модель:

```bash
docker compose down -v
```

## Локальный запуск без Docker

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
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
cd backend && pytest -q
cd ../ml_service && pytest -q
```

## Основные API

- `POST /api/v1/events/ingest` — принять событие
- `GET /api/v1/events` — список событий
- `GET /api/v1/events/{id}` — детальная карточка события
- `GET /api/v1/alerts` — список алертов
- `GET /api/v1/alerts/{id}` — детальная карточка алерта

## Логика обнаружения

1. Backend принимает JSON-лог
2. Лог нормализуется и превращается в feature vector
3. Backend отправляет признаки в ML service
4. ML service считает риск через IsolationForest
5. Если риск выше порога, backend создает alert
6. Frontend показывает события и алерты

## Ограничения прототипа

Это учебный прототип, а не промышленная SIEM-система. Для production понадобятся RBAC, HTTPS, real-time очередь, нормальные парсеры Sysmon/auditd/nginx, корреляционные правила, аудит действий пользователей и мониторинг Prometheus/Grafana.

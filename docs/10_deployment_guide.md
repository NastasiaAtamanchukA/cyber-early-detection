# Deployment Guide

## Развернутое приложение

https://cyber-early-detection.ru/

## Локальный запуск

```bash
git clone https://github.com/NastasiaAtamanchukA/cyber-early-detection.git
cd cyber-early-detection
cp .env.example .env
docker compose up --build -d
```

## Проверка

```bash
curl http://localhost:8000/api/v1/health
curl http://localhost:8001/health
```

После запуска доступны:

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- ML service: http://localhost:8001

## Демо-события

```bash
bash scripts/seed_demo.sh
```

## Остановка

```bash
docker compose down
```

Полная очистка данных:

```bash
docker compose down -v
```

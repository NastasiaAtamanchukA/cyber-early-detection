# Release notes v0.1.0

Дата: 25.05.2026

## Состав релиза

- Backend API на FastAPI для приема и просмотра событий.
- ML service на FastAPI + IsolationForest для оценки риска.
- PostgreSQL-модель данных для источников, событий, алертов и инцидентов.
- Frontend на React + TypeScript для SOC-интерфейса.
- Docker Compose для запуска проекта одной командой.
- GitHub Actions для lint/test/build.
- Документация, диаграммы, test report и deployment guide.

## Ограничения

Релиз является учебным MVP. Для production нужны RBAC, HTTPS, очередь событий, мониторинг, аудит действий и расширенные парсеры логов.

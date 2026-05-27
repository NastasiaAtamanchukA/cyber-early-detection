# Обновление проекта: расписания, рекомендации и графики

В архив добавлены доработки для демонстрации проекта на защите.

## Что изменено

1. Добавлено создание пользовательских расписаний сбора событий.
2. Добавлено редактирование существующих расписаний.
3. Добавлено включение/отключение расписаний без удаления.
4. Добавлен профиль `mixed`, который генерирует события разных типов.
5. Расширены рекомендации по действиям в инцидентах.
6. На дашборд добавлены графики:
   - donut chart по критичности алертов;
   - распределение событий по уровню риска;
   - timeline активности событий;
   - bar chart по типам событий.

## Измененные файлы

```text
backend/app/schemas.py
backend/app/api/collectors.py
backend/app/api/dashboard.py
backend/app/models.py
frontend/src/types.ts
frontend/src/api/client.ts
frontend/src/pages/CollectionPage.tsx
frontend/src/pages/DashboardPage.tsx
frontend/src/pages/IncidentsPage.tsx
frontend/src/styles.css
```

## Новые API

```http
POST /api/v1/collectors/schedules
PATCH /api/v1/collectors/schedules/{schedule_id}
POST /api/v1/collectors/schedules/{schedule_id}/run
GET /api/v1/dashboard
```

## Проверка после загрузки в GitHub

```bash
git add .
git commit -m "feat(ui): add editable schedules and dashboard charts"
git push origin main
```

После push необходимо проверить GitHub Actions: должны пройти `backend`, `ml-service`, `frontend` и `docker-build`.

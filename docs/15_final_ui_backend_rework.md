# Финальная доработка UI/backend после проверки UX

## Что исправлено

1. Дашборд пересобран в более аккуратный SOC-вид:
   - возвращена кнопка «Запустить сбор событий»;
   - добавлены KPI-карточки;
   - графики встроены без визуального перекоса;
   - добавлены блоки последних событий, алертов и инцидентов.

2. Добавлена пагинация по 10 элементов:
   - события;
   - алерты;
   - инциденты;
   - расписания сбора.

3. Добавление расписания перенесено в модальное окно:
   - форма больше не висит сверху страницы;
   - создание открывается по кнопке «Добавить расписание»;
   - редактирование открывает то же окно.

4. Возвращена фильтрация:
   - события: поиск, тип, хост, пользователь, только аномалии;
   - алерты: поиск, хост, severity, status;
   - инциденты: поиск, хост, severity, status;
   - расписания: поиск, профиль, enabled/disabled.

5. Все карточки открываются подробно:
   - событие показывает raw log и normalized log;
   - алерт показывает связанное событие;
   - инцидент показывает связанные алерты и рекомендации;
   - расписание показывает параметры и позволяет запускать сбор.

6. Реализован жизненный цикл инцидента:
   - `new/open` → кнопка «Взять в работу»;
   - `investigating` → кнопка «Закрыть»;
   - `closed` → кнопка «Переоткрыть».

7. Готовые расписания снова стабильно создают алерты и инциденты:
   - для демонстрационных высокорисковых событий задана минимальная граница риска;
   - `login_failed`, `web_attack`, `privilege_escalation`, `data_export` создают алерты;
   - high/critical и high-risk event types создают инциденты.

## Основные измененные файлы

### Backend

- `backend/app/schemas.py`
- `backend/app/api/events.py`
- `backend/app/api/alerts.py`
- `backend/app/api/incidents.py`
- `backend/app/api/dashboard.py`
- `backend/app/api/collectors.py`
- `backend/app/services/event_ingestion.py`
- `backend/tests/test_events.py`

### Frontend

- `frontend/src/types.ts`
- `frontend/src/api/client.ts`
- `frontend/src/pages/DashboardPage.tsx`
- `frontend/src/pages/EventsPage.tsx`
- `frontend/src/pages/AlertsPage.tsx`
- `frontend/src/pages/IncidentsPage.tsx`
- `frontend/src/pages/CollectionPage.tsx`
- `frontend/src/components/Pagination.tsx`
- `frontend/src/components/DetailModal.tsx`
- `frontend/src/components/JsonBlock.tsx`
- `frontend/src/styles.css`
- `frontend/Dockerfile`

## Проверка

```powershell
cd cyber-early-detection-updated-project
docker compose down --remove-orphans
docker builder prune -f
docker compose --progress=plain build frontend --no-cache
docker compose up -d --build
```

После запуска:

- frontend: http://localhost:3000
- backend health: http://localhost:8000/api/v1/health
- ML health: http://localhost:8001/health
- Swagger: http://localhost:8000/docs

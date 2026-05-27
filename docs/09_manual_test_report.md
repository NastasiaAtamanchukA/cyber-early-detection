# Отчет о ручном тестировании

| ID | Сценарий | Шаги | Ожидаемый результат | Статус |
| --- | --- | --- | --- | --- |
| MT-01 | Запуск проекта | cp .env.example .env; docker compose up --build -d | Контейнеры frontend/backend/ml/db стартуют; healthcheck успешны | Выполнить перед сдачей |
| MT-02 | Проверка backend health | curl http://localhost:8000/api/v1/health | Ответ содержит ok/healthy | Выполнить перед сдачей |
| MT-03 | Проверка ML health | curl http://localhost:8001/health | Ответ содержит ok/healthy | Выполнить перед сдачей |
| MT-04 | Отправка нормального события | POST /api/v1/events/ingest с login_success | Event создан; риск низкий; критичный alert не создается | Выполнить перед сдачей |
| MT-05 | Отправка подозрительного события | POST /api/v1/events/ingest с login_failed/bruteforce/powershell | Event создан; risk_score высокий; alert отображается | Выполнить перед сдачей |
| MT-06 | Просмотр алертов | Открыть UI Alerts или GET /api/v1/alerts | Список алертов содержит severity, title, status | Выполнить перед сдачей |
| MT-07 | Swagger | Открыть /docs | Swagger UI доступен; endpoints видны | Выполнить перед сдачей |

# Activity Diagram

```mermaid
title Диаграмма деятельности: обработка события безопасности в Cyber Early Detection

|Источник логов / Администратор|
start
:Сформировать JSON-событие безопасности;
:Отправить событие в Backend API\nPOST /api/v1/events/ingest;

|Backend API|
:Принять входящий запрос;
:Выполнить первичную проверку структуры JSON;

if (Payload корректен?) then (Да)
    :Проверить обязательные поля:\ntimestamp, host, user, event_type,\nmessage, source_name, source_kind, metadata;

    if (Обязательные поля заполнены?) then (Да)
        :Нормализовать событие;
        :Привести данные к единой модели Event;
        :Определить источник логов;

        |PostgreSQL|
        :Найти или создать LogSource;

        |Backend API|
        :Сформировать feature vector\nдля ML-анализа;

        |ML Service|
        :Получить feature vector;
        :Рассчитать risk_score;
        :Определить признак is_anomaly;
        :Вернуть результат анализа;

        |Backend API|
        :Получить risk_score и is_anomaly;

        |PostgreSQL|
        :Сохранить Event\nс результатом ML-оценки;

        |Backend API|
        if (risk_score превышает порог?) then (Да)
            :Определить severity алерта;

            |PostgreSQL|
            :Создать Alert\nи связать его с Event;

            |Backend API|
            if (Подходящий Incident найден?) then (Да)
                |PostgreSQL|
                :Связать Alert\nс существующим Incident;
                :Обновить last_seen\nи severity Incident;
            else (Нет)
                |PostgreSQL|
                :Создать новый Incident;
                :Связать Alert\nс новым Incident;
            endif

            |Backend API|
            :Сформировать успешный ответ\nс event_id, risk_score и alert_id;

        else (Нет)
            :Алерт не создается;
            :Сформировать успешный ответ\nс event_id и risk_score;
        endif

        |Источник логов / Администратор|
        :Получить ответ об успешной обработке события;

    else (Нет)
        :Сформировать ошибку валидации\nпо обязательным полям;

        |Источник логов / Администратор|
        :Получить ответ 422 Validation Error;
        stop
    endif

else (Нет)
    :Сформировать ошибку некорректного JSON;

    |Источник логов / Администратор|
    :Получить ответ 400 Bad Request;
    stop
endif

|SOC-аналитик|
:Открыть веб-интерфейс мониторинга;

|Frontend|
:Запросить список событий\nGET /api/v1/events;

|Backend API|
:Получить события из базы данных;

|PostgreSQL|
:Вернуть список Events;

|Backend API|
:Передать список событий во Frontend;

|Frontend|
:Отобразить таблицу событий;

|SOC-аналитик|
:Просмотреть события безопасности;

if (Есть подозрительные алерты?) then (Да)
    |Frontend|
    :Запросить список алертов\nGET /api/v1/alerts;

    |Backend API|
    :Получить алерты из базы данных;

    |PostgreSQL|
    :Вернуть список Alerts;

    |Frontend|
    :Отобразить список алертов\nс severity, status и title;

    |SOC-аналитик|
    :Открыть карточку алерта;
    :Проанализировать host, user,\nevent_type, message и risk_score;
    :Принять решение о дальнейшем расследовании;

else (Нет)
    |SOC-аналитик|
    :Продолжить мониторинг событий;
endif

stop
```

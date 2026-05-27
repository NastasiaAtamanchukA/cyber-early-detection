# Product Backlog

| Приоритет | Задача | Definition of Done |
| --- | --- | --- |
| P0 | Исправить падающий CI backend/ml-service | GitHub Actions заканчивается success; есть ссылка/скриншот зеленого run |
| P0 | Добавить расширенную документацию в docs | Устав, ТЗ, план, RACI, риски, user stories, backlog, deployment, test report добавлены |
| P0 | Добавить UML/ERD-диаграммы | Use Case, Class, Sequence, Activity, Component, Deployment, ERD доступны в docs/diagrams |
| P0 | Создать GitHub Release v0.1.0 | В разделе Releases опубликован v0.1.0 с notes |
| P0 | Проверить сайт и локальный Docker-запуск | Deployed URL или локальная инструкция подтверждают пункт 23 |
| P1 | Добавить 5+ автотестов | Backend/ML тесты покрывают health, ingest, list, predict, normalizer |
| P1 | Добавить раздел README "Учебный чек-лист" | В README есть ссылки на docs, CI, release, deployed URL, презентацию |
| P1 | Добавить бейдж CI в README | По бейджу видно состояние main workflow |
| P1 | Сделать demo seed стабильным | Один скрипт создает события разных уровней риска |
| P2 | Добавить фильтры в UI | SOC-аналитик фильтрует события по host/user/severity/status |
| P2 | Добавить RBAC analyst/admin | Роли отделяют просмотр от администрирования |
| P2 | Добавить расширенные парсеры Sysmon/auditd/nginx | Система принимает более реалистичные события |
| P2 | Добавить Prometheus/Grafana | Появляются метрики сервисов и контейнеров |
| P2 | Добавить корреляционные правила | Несколько событий объединяются в инцидент по временным и субъектным признакам |

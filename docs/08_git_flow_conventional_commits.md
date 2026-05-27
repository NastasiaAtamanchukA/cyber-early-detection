# Git flow и Conventional Commits

## Ветки

- `main` - стабильная ветка, из нее создается релиз.
- `dev` - интеграционная ветка разработки.
- `feature/<name>` - новые функции.
- `fix/<name>` - исправления ошибок.
- `docs/<name>` - документация и схемы.
- `release/v0.1.0` - финальная подготовка релиза.

## Формат коммитов

`<type>(scope): <description>`

Примеры:

```bash
git commit -m "docs(project): add detailed charter and technical specification"
git commit -m "fix(ci): make backend and ml tests pass"
git commit -m "test(api): add ingest and health endpoint tests"
git commit -m "chore(release): prepare v0.1.0 notes"
```

## Процесс релиза

1. Исправить CI до зеленого состояния.
2. Добавить документы и схемы в репозиторий.
3. Обновить README ссылками на docs, сайт, CI и release.
4. Создать тег `v0.1.0`.
5. Создать GitHub Release через интерфейс GitHub.

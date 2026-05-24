# Quality Gates Template

Этот файл нужно адаптировать под новый проект.

## Architecture Gates

- Vision, Scope, Conceptual Design and Solution Design не конфликтуют.
- Новое архитектурное решение имеет ADR.
- Общий core не содержит предметных терминов конкретной вертикали, если продукт модульный.
- Все внешние сервисы описаны до подключения.

## Product Gates

- MVP решает конкретную боль.
- Основной пользовательский путь описан.
- Критерии успеха измеримы.
- Отложенные функции явно вынесены из Scope.

## Security Gates

- ПД не отправляются в LLM.
- Секреты не читаются и не логируются.
- Доступ к данным проверяется сервером.
- Tenant/project/user isolation описана, если нужна.

## AI Gates

- Все AI-вызовы идут через AI gateway.
- AI output проверяется схемой.
- AI не является источником истины для денег, права, медицины, безопасности or critical decisions.
- Sensitive payload очищается до AI provider.

## UI Gates

- Есть общий visual/design foundation.
- Основные экраны имеют desktop/mobile states.
- Ошибки и пустые состояния описаны.
- Пользователь видит следующий шаг.

## Backend Gates

- API contracts описаны до реализации.
- Idempotency есть для повторяемых side effects.
- Audit есть для критичных действий.
- Миграции не разрушительные без approval.

## QA Gates

- Каждая task имеет evidence.
- `passed` только после запуска проверки.
- `not_run` всегда с причиной.
- Критичные gates блокируют следующий slice.


# Architect Inbox

Это локальное рабочее пространство, куда AI-сотрудники кладут запросы твоего вмешательства.

## Где лежат запросы

Обычные решения архитектора:

```text
workspace/architect-inbox/requests/ARCH-REQUEST-YYYYMMDD-TASK-ID-short-slug.json
```

Специализированные запросы реального прайса:

```text
reports/price-requests/PRICE-REQUEST-YYYYMMDD-TASK-ID.json
```

## Как смотреть

```bash
python3 harness/scripts/architect_inbox.py
python3 harness/scripts/architect_inbox.py --json
```

## Как отвечать

Минимальный рабочий порядок:

1. Открой request.
2. Прими решение в ответе AI-сотруднику или в отдельном документе.
3. Если решение архитектурное, создай/обнови ADR.
4. После фиксации решения можно перенести request в `workspace/architect-inbox/archive/`.

Request не должен содержать секреты, `.env`, реальные ПД или полный реальный прайс.

# Task And Evidence Protocol

## Главное

AI-сотрудник берет не большую задачу, а маленькую micro-task.

Плохо:

```text
Сделай весь MVP.
```

Хорошо:

```text
Сделай TASK-003A: описать data model для MVP.
```

## Task card

Каждая task card должна содержать:

- `id`;
- `title`;
- `role`;
- `owner`;
- `status`;
- `slice`;
- `work_package`;
- `source_docs`;
- `goal`;
- `inputs`;
- `outputs`;
- `constraints`;
- `forbidden`;
- `gate_ids`;
- `required_evidence`;
- `required_reports`;
- `dependencies`;
- `handoff_to`;
- `acceptance`.

## Evidence report

Задача считается завершенной только после:

```text
reports/task-evidence/TASK-ID.json
```

Если проверка не запускалась, писать:

```json
{ "status": "not_run", "reason": "..." }
```

Нельзя писать `passed`, если проверка не запускалась.

## Stop rules

AI-сотрудник останавливается, если:

- нужно изменить Scope;
- нужны реальные ПД;
- нужны реальные деньги/цены/медицинские/юридические данные;
- нужен внешний сервис;
- нужен deploy/publish;
- task не имеет gates;
- dependency не закрыта;
- нет нужного решения человека.

## Human request

Если нужно решение человека, создается:

```text
workspace/architect-inbox/requests/ARCH-REQUEST-*.json
```

Если нужны реальные данные:

```text
workspace/architect-inbox/requests/EXTERNAL-INPUT-REQUEST-*.json
```


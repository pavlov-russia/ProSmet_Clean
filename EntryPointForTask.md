# EntryPointForTask.md

Это входная точка для любой новой задачи AI-сотрудника.

## 1. Перед стартом

Прочитай:

1. `AGENTS.md`
2. `CLAUDE.md`, если работа идет в Claude Code
3. `docs/AI_M_MSF.md`
4. `Focus.md`
5. `Team.yml`
6. `docs/Context/2026-05-19-autonomous-mvp-feedback.md`
7. `docs/Context/2026-05-23-ai-team-implementation-architecture.md`, если задача касается AI-команды, orchestrator, gates, evidence, task protocol или harness
8. `Scope.md`
9. `docs/dev/ImplementationPlan.md`
10. `docs/dev/PredictableAIWork.md`
11. `docs/Evals/GateMatrix.md`
12. Свою карточку задачи из `tasks/`

## 2. Определи тип задачи

- Vision / Scope
- Conceptual Design
- Solution Design
- Architecture / ADR
- Autonomous offer mode
- Domain model
- Estimation engine
- AI flow
- Frontend
- Backend
- QA / eval
- DevOps

## 3. Выбери роль

Роль берется из `Team.yml` и раскрывается в `harness/build-team.md`.

## 4. Проверь границы

Если задача расширяет `Scope.md`, остановись и задай вопрос архитектору.

Если задача меняет архитектурный инвариант, создай или обнови ADR.

Если задача касается смет, проверь `docs/Domain/DeterministicEstimation.md`.

Если задача касается API, данных, RLS, расчета, AI gateway или публикации, проверь соответствующий contract-file в `docs/contracts/`.

Если задача является implementation-задачей, проверь, что карточка содержит `slice`, `work_package`, `gate_ids`, `required_evidence`, `required_reports` и `acceptance`. Если этого нет, задача не готова к исполнению.

Если задача ссылается на `gate_ids`, проверь их в `docs/Evals/gates.json`.

Если задача требует вмешательства архитектора из списка Ask First (`Scope`, вертикаль, production dependency, бизнес-модель, legal promise, destructive migration, deploy/publish, external service, real PII, pilot data, external architecture source), создай `workspace/architect-inbox/requests/ARCH-REQUEST-YYYYMMDD-TASK-ID-short-slug.json` по `docs/contracts/ArchitectInterventionRequest.md` и явно попроси архитектора ответить.

Если для продолжения нужен реальный прайс, коэффициенты, минимальный заказ, округления, скидочная политика или expert-approved golden totals, не придумывай значения. Создай `reports/price-requests/PRICE-REQUEST-YYYYMMDD-TASK-ID.json` по `docs/contracts/PriceInputRequest.md` и явно попроси архитектора внести прайс.

## 5. Завершение задачи

В конце работы:

- перечисли измененные файлы;
- укажи, какие проверки выполнены;
- создай или обнови machine-readable evidence report из `required_reports`;
- если нужен ответ архитектора, укажи путь к созданному `ArchitectInterventionRequest`;
- если нужен реальный прайс, укажи путь к созданному `PriceInputRequest`;
- вынеси нерешенные вопросы в `Backlogs.md`;
- если нужно, создай handoff в `docs/dev/handoffs/`.

Нельзя писать, что gate пройден, если команда не запускалась. Используй `not_run` с причиной.

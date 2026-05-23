# ADR-008 · Deterministic approval policy protocol

Дата: 2026-05-19  
Статус: принято  
Связано: `docs/ADR/ADR-007-autonomous-offer-mode.md`, `docs/Domain/DeterministicEstimation.md`

## Контекст

Autonomous offer mode требует автоматической публикации типовых заявок, но решение публикации не может принимать LLM. Нужен отдельный deterministic policy layer, который проверяет readiness tenant, полноту данных, legal gates, phone-gate, AI confidence, risk flags и immutable calculation snapshot.

После уточнения архитектора от 2026-05-19 отсутствие части данных не должно полностью убивать расчет. ProSmet должен показывать частичную смету, где неизвестные блоки явно помечены как "недостаточно данных".

## Решение

Вводим `ApprovalPolicyService`.

Сервис получает только уже созданный immutable calculation snapshot и проверочные признаки:

- tenant readiness;
- legal/consent state;
- phone-gate state;
- required fields completeness;
- calculation completeness: `complete`, `partial`, `unusable`;
- AI confidence;
- AI risk flags;
- calculation risk flags;
- contradictions;
- manual adjustments;
- policy profile.

Сервис не считает цену, не вызывает LLM и не меняет расчет.

Порядок решений:

1. Если нет immutable calculation snapshot -> `requires_review`.
2. Если расчет `unusable` и нет даже честного skeleton estimate -> `reject_as_incomplete`.
3. Если нет consent -> `reject_as_incomplete`.
4. Если phone-gate включен и нет телефона -> полная публикация блокируется; preview остается доступным, policy decision для полной публикации не проходит.
5. Если autonomous mode выключен -> `requires_review`.
6. Если price/pricing profile/formula/legal/notification readiness неполный -> `requires_review`.
7. Если есть measurement risk flags -> `requires_measurement`.
8. Если есть contradictions, manual adjustments или review risk flags -> `requires_review`.
9. Если AI confidence ниже threshold -> `requires_review`.
10. Если расчет complete -> `auto_publish` с `publicationMode = full`.
11. Если расчет partial, tenant разрешает partial publication и все неизвестные блоки явно показаны как "недостаточно данных" -> `auto_publish` с `publicationMode = partial`.
12. Иначе -> `requires_review`.

Начальный conservative profile:

- `min_ai_confidence = 0.90`;
- unusable calculation -> `reject_as_incomplete`;
- partial calculation ниже tenant completeness threshold -> `requires_review`;
- partial calculation выше threshold и без blocking flags -> `auto_publish` с `publicationMode = partial`;
- any contradiction -> `requires_review`;
- complex geometry without perimeter -> `requires_measurement`;
- height above supported threshold -> `requires_measurement`;
- 8+ corners without perimeter -> `requires_measurement`;
- more than 20 spotlights -> `requires_review`;
- fabric with flooding history -> `requires_review`;
- individual discount request -> `requires_review`;
- commercial object -> `requires_review` or `requires_measurement` by tenant profile.

Понижение threshold или ослабление blocking flags требует отдельной пилотной приемки.

## Последствия

- `approval_policy_decisions` становится обязательной таблицей.
- Каждое решение хранит `policy_version`, `policy_profile_id`, `input_hash`, `calculation_id`, `risk_flags`, `ai_confidence`, `reason_codes`.
- Каждое решение хранит `publicationMode`, если decision = `auto_publish`.
- Publication workflow fail-closed: при ошибке policy engine заявка идет в `requires_review`.
- Quality gates должны покрывать каждый blocking gate.
- SeniorCeilingEstimator отвечает за предметную ревизию risk flags, но не принимает решение `auto_publish`.

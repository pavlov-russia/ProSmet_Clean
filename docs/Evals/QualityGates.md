# QualityGates.md

Дата: 2026-05-19  
Статус: обязательные проверки MVP, обновлено под autonomous MVP feedback

## 1. Calculation Gates

- Один и тот же ввод дает один и тот же результат 100 раз подряд.
- Эконом дешевле стандарта, стандарт дешевле премиума.
- Фиксированные строки не умножаются на коэффициенты сложности.
- Множитель работы не превышает верхний предел.
- Изменение версии прайса не меняет старую сохраненную смету.
- Отсутствующие обязательные параметры создают partial estimate с `insufficient_data` строками или требуют уточнения, если расчет полностью непригоден.
- Нестандартный случай помечается как требующий замера.
- PDF содержит версию формулы и прайса.
- Policy decision не меняет расчетные суммы.
- `auto_publish` невозможен без immutable calculation snapshot.
- Partial estimate не показывает неполный итог как финальную полную стоимость.

## 2. AI Gates

- В payload к LLM нет телефона, имени, email, адреса.
- В payload к LLM нет денежных сумм и price-полей.
- При недостающих данных AI задает вопрос.
- При противоречии AI просит уточнение.
- AI-ответ не обещает окончательную цену до замера.
- Любой расчетный вывод ссылается на результат формулы, а не на догадку модели.
- Все AI-вызовы проходят через `packages/core/ai/gateway`.
- Senior AI-сметчик не возвращает price, discount, coefficient value, line amount или final total.
- AI может вернуть risk flags и missing fields, но не решение о цене.

## 3. Security Gates

- Tenant определяется серверной сессией.
- API игнорирует `tenantId` из body, query, localStorage и `postMessage`.
- RLS включен на чувствительных таблицах.
- Приложение не имеет `BYPASSRLS`.
- Tenant A не читает данные tenant B.
- Доступ к оригиналу ПД пишет запись в `pii_access_log`.
- Согласие записано до сбора ПД.
- Preview до телефона замыливает итоговые/ценовые блоки по tenant policy.
- Телефон записан до полного раскрытия уникальной клиентской сметы/PDF, если tenant включает phone-gate.

## 4. PDF and Client Link Gates

- Документ создается после human review или audited `auto_publish`.
- PDF создается только после полного раскрытия и phone-gate, если phone-gate включен.
- Есть бренд бригады.
- Есть дата.
- Есть версия расчета.
- Есть версия прайса.
- Есть параметры помещения.
- Есть строки материалов и работ.
- Есть срок действия.
- Есть фраза: "не является публичной офертой (ст. 437 ГК РФ). Окончательные условия определяются в договоре по результатам замера."
- Клиентская ссылка уникальна и не раскрывает tenant/private identifiers.
- Открытие ссылки пишет событие `opened`.
- Повторное открытие пишет событие `reopened` или обновляет счетчик с audit.
- Скачивание PDF пишет событие `pdf_downloaded`.
- Клик по следующему шагу пишет событие `cta_clicked`.

## 5. Autonomous Offer Gates

- Autonomous offer mode включен явно на tenant.
- Tenant имеет настроенный прайс, формулы, legal pack и канал уведомлений.
- Все обязательные расчетные параметры заполнены или partial estimate разрешен tenant policy и все missing blocks явно показаны клиенту.
- AI confidence выше порога, утвержденного архитектором.
- Нет противоречий, risk flags, ручных скидок и сложной геометрии.
- Policy decision записан в `approval_policy_decisions`.
- `auto_publish` создает клиентскую ссылку/PDF только из immutable snapshot.
- `auto_publish` с partial estimate хранит `publicationMode = partial`.
- Нестандартная заявка уходит в `requires_review` или `requires_measurement`.
- Владелец видит новый лид, статус, открытие ссылки и скачивание PDF.

## 6. Channel Gates

- Вход с сайта проверяет tenant domain и allowed origins.
- Вход из Авито фиксирует source/channel без доверия к tenant из URL как к единственному источнику.
- Виджет собирает параметры как чат с быстрыми ответами и собственным вводом.
- Telegram/Max-уведомление не содержит ПД и денежных сумм сверх разрешенного шаблона.
- Если чат-бот недоступен, событие остается в web-кабинете и notification queue.

## 7. Architecture Gates

- `packages/core` не содержит потолочных терминов.
- Потолочные формулы и prompts живут в `apps/ceiling/domain`.
- Прямые AI-вызовы вне gateway отсутствуют.
- Policy engine не вызывает LLM.
- Прямой импорт `db` в приложении отсутствует, кроме разрешенного слоя.
- Новое архитектурное решение имеет ADR.
- Детерминированный расчет соответствует `docs/Domain/DeterministicEstimation.md`.

## 8. AI Build Team Gates

- Исполняемая task card содержит `slice`, `work_package`, `gate_ids`, `required_evidence`, `required_reports` и `acceptance`.
- Все `gate_ids` существуют в `docs/Evals/gates.json`.
- Wide work packages `TASK-002`...`TASK-010` не dispatch'ятся напрямую; работу выполняют micro-tasks.
- Каждая завершенная task имеет evidence report в `reports/task-evidence/`.
- Gate нельзя отметить как passed без запущенной проверки или explicit evidence.
- Межslice переход требует QA/Architect acceptance checkpoint.
- Synthetic fixtures не подменяют реальный пилотный прайс или legal approval.
- AIOrchestrator выпускает command packets только после явного approval архитектора.
- Orchestrator proposal блокируется на failed validations, blocking inbox requests and missing process gates.
- Orchestrator approval повторно проверяет Architect Inbox, чтобы новый blocker не обошел старым proposal.

## 9. Visual and Marketing Site Gates

- Visual tokens зафиксированы до реализации UI.
- Основная палитра: белый, светло-голубой, мягкий фиолетовый accent, темный текст.
- Marketing site ProSmet отделен от tenant/customer runtime data.
- Marketing site использует только synthetic screenshots/demo data до отдельного approval на реальные материалы.
- Demo/pilot lead form получает consent до phone/email/name.
- Marketing payload не отправляется в LLM.
- Marketing site не обещает точную цену, скидку, ROI or legal guarantees без подтвержденного contract/legal review.
- Production deploy, external analytics and external form provider требуют отдельного ArchitectInterventionRequest.

## 10. Edge Cases

- площадь 0 или отрицательная;
- углов меньше 4;
- очень большая площадь;
- высота больше 4 м;
- больше 20 светильников;
- ткань при истории потопов;
- срочный монтаж;
- коммерческий объект;
- неполный ввод клиента;
- противоречивый ввод клиента;
- клиент просит "подешевле";
- менеджер меняет скидку;
- устаревший прайс;
- клиент открыл ссылку несколько раз;
- клиент скачал PDF без следующего шага;
- клиент пришел из Авито без полного описания помещения;
- Telegram/Max-уведомление не доставлено;
- tenant отключил autonomous offer mode.
- клиент увидел preview, но не оставил телефон;
- partial estimate содержит несколько `insufficient_data` блоков;
- local/VPS окружение не должно принимать реальные ПД без решения.

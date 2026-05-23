# DeterministicEstimation.md

Дата: 2026-05-19  
Статус: архитектурный инвариант ProSmet, обновлено под autonomous offer mode

## 1. Цель

Сметы ProSmet должны считаться воспроизводимо.

Это означает:

- один и тот же вход;
- та же версия формулы;
- тот же snapshot прайса;
- та же дата расчета, если дата влияет на сезонность;
- тот же региональный набор коэффициентов;

дают один и тот же результат любое количество раз.

## 2. Что значит "100% правильно"

Архитектура может гарантировать детерминированность, трассируемость и отсутствие произвола AI.

Фактическая правильность цены зависит от:

- корректности входных параметров;
- качества прайса;
- проверенности формул;
- экспертной валидации golden estimates;
- человеческой проверки в режиме калибровки и исключений;
- deterministic policy gates перед автономной публикацией.

Поэтому цель формулируется так:

```text
Расчет всегда воспроизводим, объясним и проверяем.
AI никогда не является источником цены.
Правильность повышается через golden estimates, реальные прайсы, regression tests, human review и approval policy gates.
```

## 3. Запрет на LLM в расчете

LLM не участвует в расчетной функции.

LLM может вернуть только структуру:

```ts
type EstimateDraftParams = {
  roomType?: string;
  areaSqm?: number;
  shape?: string;
  fabricType?: string;
  fabricBrand?: string;
  cornersCount?: number;
  heightM?: number;
  spotLightsCount?: number;
  chandelierCount?: number;
  assumptions: string[];
  missingFields: string[];
  riskFlags: string[];
  confidence: number;
};
```

Запрещенные поля в AI output:

- `price`;
- `priceRub`;
- `finalPrice`;
- `discount`;
- `margin`;
- `coefficientValue`;
- `estimateLineAmount`;
- `total`;

Schema validator должен отклонять или вычищать такие поля.

## 4. Calculation Engine

Calculation engine — pure module.

Вход:

```ts
type CalculationInput = {
  normalizedParams: CeilingEstimateParams;
  priceBookSnapshot: PriceBookSnapshot;
  formulaVersion: string;
  coefficientSnapshot: CoefficientSnapshot;
  calculationDate: ISODate;
};
```

Выход:

```ts
type CalculationResult = {
  calculationId: string;
  formulaVersion: string;
  priceBookVersion: string;
  priceBookHash: string;
  inputHash: string;
  completenessStatus: "complete" | "partial" | "unusable";
  completenessScore: number;
  missingBlocks: string[];
  variants: EstimateVariant[];
  warnings: CalculationWarning[];
  assumptions: CalculationAssumption[];
  riskFlags: CalculationRiskFlag[];
  auditTrail: CalculationAuditStep[];
};
```

Запрещено внутри engine:

- сетевые вызовы;
- LLM-вызовы;
- чтение БД;
- текущий `Date.now()` без явной передачи даты;
- случайность;
- скрытые mutable globals;
- округления без правил.

## 5. Money Model

Деньги хранятся:

- в копейках как integer; или
- в decimal/numeric с явной политикой округления.

Правила:

- никакого float для денег;
- округление только в одном модуле;
- каждая строка сметы хранит количество, единицу, цену за единицу, сумму и источник;
- итог считается из строк, а не вводится руками.

## 6. Price Snapshot

Прайс нельзя читать "живым" при просмотре старой сметы.

Каждый расчет сохраняет:

- `price_book_id`;
- `price_book_version`;
- `price_book_hash`;
- snapshot использованных price items;
- snapshot coefficient values;
- formula version.

После изменения прайса старая смета остается прежней.

Новая смета создается как новый расчет.

## 7. Formula Registry

Формулы версионируются:

```text
ceiling.v1.area
ceiling.v1.materials
ceiling.v1.work
ceiling.v1.fixed-lines
ceiling.v1.variants
```

Каждая версия формулы имеет:

- changelog;
- тесты;
- список поддерживаемых параметров;
- правила fallback;
- правила блокировки расчета.

## 8. Partial and Blocking Rules

Расчет не исчезает, если нет части обязательных данных.

Engine должен вернуть:

- рассчитанные строки по известным данным;
- строки со статусом `insufficient_data` для непосчитанных блоков;
- `completenessStatus = partial`;
- список `missingBlocks`;
- warnings и assumptions.

Расчет становится `unusable`, если нет даже минимальной основы для честного skeleton estimate.

Критичные поля для полного расчета:

- регион;
- тип помещения;
- площадь;
- тип полотна;
- бренд полотна;
- количество углов;
- высота;
- световые точки / люстра.

Расчет помечается как `partial` или policy-level `requires_measurement`, если:

- геометрия сложная и нет периметра;
- высота выше поддерживаемого порога;
- площадь выходит за допустимый диапазон;
- есть противоречия;
- накопленный множитель сложности выше лимита;
- данные пришли с низкой уверенностью AI.

## 9. Approval Policy Contract

После расчета отдельный deterministic policy layer принимает одно из решений:

- `auto_publish` — типовая заявка может получить клиентскую ссылку и PDF без ручного действия компании;
- `requires_review` — нужна проверка владельца, менеджера или сметчика;
- `requires_measurement` — нужна очная проверка или замер;
- `reject_as_incomplete` — данных недостаточно даже для skeleton/partial estimate.

Policy layer получает:

- immutable calculation snapshot;
- список обязательных и заполненных параметров;
- completeness status и missing blocks;
- warnings и risk flags;
- AI confidence и missing fields;
- наличие согласия и телефона, если включен phone-gate;
- tenant-настройку autonomous offer mode;
- legal pack version.

Policy layer не считает цены и не вызывает LLM. Решение сохраняется в audit trail.

## 10. Human Review Contract

До отправки клиенту человек видит:

- входные параметры;
- недостающие поля;
- допущения;
- warnings;
- строки сметы;
- примененные коэффициенты;
- источник цены каждой строки;
- версию формулы;
- версию прайса;
- дату расчета.

В MVP-0 и первых пилотах PDF или ссылка создаются только после approve. В product-ready autonomous MVP PDF или ссылка также могут создаваться после `auto_publish`, если решение policy layer аудировано и привязано к immutable calculation snapshot.

## 11. Regression Set

Обязательный набор:

- 5-10 golden estimates до старта engine;
- 50+ unit tests после стабилизации formula v1;
- property tests на границы;
- snapshot tests для PDF/link;
- tests на approval policy decisions;
- tests на запрет `auto_publish` при risk flags;
- tests на запрет price fields в AI output;
- test "same input 100 times".
- tests на partial estimate и `insufficient_data` строки.

## 12. Audit Trail

Каждая строка результата должна отвечать на вопрос:

```text
Почему эта сумма появилась в смете?
```

Минимальный audit step:

```yaml
line_id:
source: price_item | formula | fixed_rule | manual_adjustment
rule_id:
input:
calculation:
result:
```

Manual adjustment допустим только после human review и должен хранить автора, причину и время.

Auto-publish audit step:

```yaml
decision_id:
decision: auto_publish | requires_review | requires_measurement | reject_as_incomplete
policy_version:
input_hash:
calculation_id:
risk_flags:
confidence:
legal_pack_version:
result:
```

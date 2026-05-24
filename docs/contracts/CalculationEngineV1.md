# CalculationEngineV1.md

Дата: 2026-05-23  
Статус: контракт v1 для реализации calculation engine  
Связано: `docs/Domain/DeterministicEstimation.md`, `docs/Domain/CeilingEstimateModel.md`, `docs/SolutionDesign.md`, `docs/Evals/QualityGates.md`

## 1. Назначение

`CalculationEngineV1` описывает чистый расчетный контракт ProSmet.

Engine принимает уже нормализованные параметры, immutable snapshots прайса, коэффициентов, pricing profile, markup policy и версию формул. Engine возвращает воспроизводимый расчет с вариантами, строками, статусом полноты и audit trail.

Engine не загружает данные сам. Сервисный слой отвечает за tenant scope, загрузку snapshot из БД, сохранение результата и publication workflow.

## 2. Инварианты

- Один и тот же `CalculationInput` всегда дает один и тот же `CalculationResult`.
- LLM не участвует в расчете, не выбирает коэффициенты и не создает строки сметы.
- Engine не делает сетевые вызовы, DB reads, filesystem reads, `Date.now()` и random.
- Денежные значения передаются в minor units, без float.
- Старый расчет зависит только от сохраненных snapshots, а не от текущего прайса tenant.
- Формулы, прайс, коэффициенты и rounding policy версионируются и хэшируются.
- Каждая amount-bearing строка имеет audit step с источником цены, правилом и входом.

## 3. TypeScript-like Contracts

```ts
type ISODate = string; // YYYY-MM-DD
type ISODateTime = string; // ISO-8601 UTC
type Hash = string; // sha256 over canonical JSON
type TenantId = string;
type LeadId = string;
type RoomId = string;
type CalculationId = string;
type CurrencyCode = "RUB";
type JsonScalar = string | number | boolean | null;
type JsonValue = JsonScalar | JsonObject | JsonValue[];
type JsonObject = { [key: string]: JsonValue };

type MinorUnitAmount = string; // base-10 integer string, e.g. "125000"

type MoneyMinor = {
  amountMinor: MinorUnitAmount;
  currency: CurrencyCode;
};

type DecimalString = string; // base-10 decimal string, never JS float for money or coefficients

type CalculationInput<TParams extends JsonObject = JsonObject> = {
  contractVersion: "calculation-engine.v1";
  tenantId: TenantId; // server-side tenant scope only; not trusted from client payload
  leadId?: LeadId;
  roomId?: RoomId;
  calculationDate: ISODate;
  vertical: "ceiling";
  normalizedParams: TParams;
  formulaRegistryManifest: FormulaRegistryManifestV1;
  formulaVersion: string;
  priceBookSnapshot: PriceBookSnapshot;
  coefficientSnapshot: CoefficientSnapshot;
  tenantPricingProfileSnapshot: TenantPricingProfileSnapshot;
  markupPolicySnapshot: MarkupPolicySnapshot;
  requestMeta: {
    source: "manual_owner_input" | "widget" | "avito_entry" | "api" | "test_fixture";
    idempotencyKey?: string;
    aiConfidence?: DecimalString | null; // copied for completeness/risk only, not for price
    aiRiskFlags?: string[];
    missingFields?: string[];
    assumptions?: string[];
    contradictions?: string[];
  };
};

type CalculationResult = {
  contractVersion: "calculation-engine.v1";
  calculationId: CalculationId;
  tenantId: TenantId;
  leadId?: LeadId;
  roomId?: RoomId;
  vertical: "ceiling";
  formulaVersion: string;
  formulaRegistryHash: Hash;
  priceBookId: string;
  priceBookVersion: string;
  priceBookHash: Hash;
  coefficientSetId: string;
  coefficientSnapshotHash: Hash;
  tenantPricingProfileSnapshotHash: Hash;
  markupPolicySnapshotHash: Hash;
  inputHash: Hash;
  resultHash: Hash;
  calculationDate: ISODate;
  completenessStatus: "complete" | "partial" | "unusable";
  completenessScore: DecimalString; // 0.0000..1.0000
  missingBlocks: MissingBlock[];
  warnings: CalculationWarning[];
  assumptions: CalculationAssumption[];
  riskFlags: CalculationRiskFlag[];
  variants: EstimateVariant[];
  auditTrail: AuditStep[];
};

type MissingBlock = {
  blockId: string;
  label: string;
  requiredFor: "full_total" | "variant" | "line_item" | "policy";
  missingFields: string[];
  visibleToClientAs: "insufficient_data";
};

type CalculationWarning = {
  code: string;
  severity: "info" | "warning" | "blocking_for_auto_publish";
  message: string;
  relatedFields?: string[];
};

type CalculationAssumption = {
  code: string;
  message: string;
  source: "domain_default" | "tenant_default" | "formula_rule" | "ai_gateway";
};

type CalculationRiskFlag = {
  code: string;
  category: "requires_review" | "requires_measurement" | "blocks_calculation";
  message: string;
  source: "formula_rule" | "domain_rule" | "ai_gateway";
};
```

### 3.1. PriceBookSnapshot

```ts
type PriceBookSnapshot = {
  snapshotType: "price_book";
  priceBookId: string;
  tenantId: TenantId;
  vertical: "ceiling";
  version: string;
  hash: Hash;
  currency: CurrencyCode;
  validFrom: ISODate;
  capturedAt: ISODateTime;
  sourceImportId?: string;
  items: PriceBookItemSnapshot[];
};

type PriceBookItemSnapshot = {
  priceItemId: string;
  sku: string;
  kind:
    | "material"
    | "work"
    | "fixed_material"
    | "fixed_work"
    | "service"
    | "delivery"
    | "measurement";
  category: string;
  label: string;
  unit: "sqm" | "m" | "piece" | "room" | "order" | "hour";
  unitPrice: MoneyMinor;
  taxMode: "included" | "excluded" | "not_applicable";
  metadata: JsonObject; // no PII
  effectiveStatus: "active" | "deprecated";
};
```

### 3.2. CoefficientSnapshot

```ts
type CoefficientSnapshot = {
  snapshotType: "coefficient_set";
  coefficientSetId: string;
  tenantId: TenantId;
  vertical: "ceiling";
  version: string;
  hash: Hash;
  capturedAt: ISODateTime;
  coefficients: CoefficientValueSnapshot[];
};

type CoefficientValueSnapshot = {
  coefficientId: string;
  code: string;
  label: string;
  value: DecimalString;
  appliesTo: "work" | "materials" | "variant" | "line_item" | "eligibility_only";
  ruleId: string;
  source: "tenant_profile" | "formula_default" | "expert_rule";
  metadata: JsonObject; // no PII, no free-form price explanation
};
```

### 3.3. TenantPricingProfileSnapshot

```ts
type TenantPricingProfileSnapshot = {
  snapshotType: "tenant_pricing_profile";
  pricingProfileId: string;
  tenantId: TenantId;
  version: string;
  hash: Hash;
  priceBookId: string;
  priceBookVersion: string;
  coefficientSetId: string;
  coefficientSetVersion: string;
  markupPolicyId: string;
  markupPolicyVersion: string;
  minimumOrderAmount: MoneyMinor | null;
  roundingPolicy: RoundingPolicySnapshot;
  estimateValidityDays: number;
  measurementFeePolicy: {
    mode: "not_configured" | "free" | "fixed" | "credited_after_contract";
    amount?: MoneyMinor;
  };
  capturedAt: ISODateTime;
};

type RoundingPolicySnapshot = {
  mode: "none" | "nearest_minor" | "nearest_10_rub" | "nearest_50_rub" | "nearest_100_rub";
  direction: "nearest" | "up" | "down";
  applyAt: "line" | "variant_total" | "both";
};
```

### 3.4. MarkupPolicySnapshot

```ts
type MarkupPolicySnapshot = {
  snapshotType: "markup_policy";
  markupPolicyId: string;
  tenantId: TenantId;
  version: string;
  hash: Hash;
  capturedAt: ISODateTime;
  globalMarkupBps: number; // basis points, 1500 = 15.00%
  categoryMarkupBps: Record<string, number>;
  marginFloorBps: number | null;
  discountPolicy: {
    manualDiscountAllowed: boolean;
    maxManualDiscountBps?: number;
    requiresHumanReview: true;
  };
};
```

### 3.5. EstimateVariant, CalculationItem, AuditStep

```ts
type EstimateVariant = {
  variantId: string;
  code: "economy" | "standard" | "premium";
  label: string;
  status: "complete" | "partial" | "unavailable";
  knownSubtotal: MoneyMinor;
  finalTotal: MoneyMinor | null; // null unless status = "complete"
  currency: CurrencyCode;
  items: CalculationItem[];
  missingBlocks: string[];
  warnings: string[];
  summary: JsonObject;
};

type CalculationItem = {
  itemId: string;
  variantCode: "economy" | "standard" | "premium";
  kind:
    | "material"
    | "work"
    | "fixed_material"
    | "fixed_work"
    | "service"
    | "discount"
    | "insufficient_data";
  label: string;
  quantity: DecimalString | null;
  unit: "sqm" | "m" | "piece" | "room" | "order" | "hour" | "unknown";
  unitPrice: MoneyMinor | null;
  amount: MoneyMinor | null;
  calculationStatus: "calculated" | "insufficient_data" | "not_applicable";
  insufficientDataReason?: {
    code: string;
    message: "недостаточно данных";
    missingFields: string[];
    blocksFullTotal: boolean;
  };
  sourceRef: {
    priceItemId?: string;
    priceSku?: string;
    formulaId?: string;
    coefficientIds?: string[];
    ruleId: string;
  };
  auditStepIds: string[];
};

type AuditStep = {
  auditStepId: string;
  lineItemId?: string;
  variantCode?: "economy" | "standard" | "premium";
  source: "price_item" | "formula" | "coefficient" | "fixed_rule" | "rounding" | "minimum_order" | "insufficient_data";
  ruleId: string;
  formulaId?: string;
  input: JsonObject;
  calculation: JsonObject;
  result: JsonObject;
  sourceSnapshot: {
    priceBookHash?: Hash;
    coefficientSnapshotHash?: Hash;
    formulaRegistryHash?: Hash;
    tenantPricingProfileSnapshotHash?: Hash;
    markupPolicySnapshotHash?: Hash;
  };
};
```

## 4. Formula Registry Manifest v1

Formula registry хранит список формул и правил, которые engine может выполнить. Manifest является частью `CalculationInput` и хэшируется вместе с расчетом.

```ts
type FormulaRegistryManifestV1 = {
  manifestVersion: 1;
  registryId: string;
  vertical: "ceiling";
  formulaVersion: string; // e.g. "ceiling.v1"
  formulaRegistryHash: Hash;
  status: "draft" | "approved" | "deprecated";
  supportedEngineContract: "calculation-engine.v1";
  supportedParamsSchemaId: string;
  formulas: FormulaManifestEntry[];
  partialRules: PartialRuleManifestEntry[];
  blockingRules: BlockingRuleManifestEntry[];
  roundingPolicyCompatibility: string[];
  changelog: {
    version: string;
    date: ISODate;
    summary: string;
  }[];
};

type FormulaManifestEntry = {
  formulaId: string; // e.g. "ceiling.v1.area"
  version: string;
  label: string;
  inputs: string[];
  outputs: string[];
  requiredPriceCategories: string[];
  requiredCoefficientCodes: string[];
  supportsVariants: ("economy" | "standard" | "premium")[];
  fallbackBehavior: "insufficient_data_line" | "not_applicable" | "block_calculation";
  tests: string[];
};

type PartialRuleManifestEntry = {
  ruleId: string;
  missingFields: string[];
  affectedBlocks: string[];
  itemBehavior: "emit_insufficient_data_item" | "omit_not_applicable";
  resultStatus: "partial" | "unusable";
};

type BlockingRuleManifestEntry = {
  ruleId: string;
  condition: string;
  result:
    | "unusable"
    | "risk_requires_review"
    | "risk_requires_measurement"
    | "warning_only";
  riskFlagCode?: string;
};
```

Canonical formula ids for MVP:

- `ceiling.v1.area`
- `ceiling.v1.materials`
- `ceiling.v1.work`
- `ceiling.v1.fixed-lines`
- `ceiling.v1.variants`
- `ceiling.v1.rounding`
- `ceiling.v1.minimum-order`
- `ceiling.v1.partial-rules`

## 5. Partial and Unusable Semantics

`complete`:

- Все обязательные amount-bearing блоки рассчитаны.
- Все варианты имеют `status = "complete"`.
- `finalTotal` заполнен для каждого publishable варианта.
- `missingBlocks` пустой или содержит только непубликуемые подсказки.

`partial`:

- Есть достаточная основа для честного skeleton estimate.
- Известные строки рассчитаны deterministic engine.
- Неизвестные amount-bearing блоки представлены `CalculationItem` со статусом `insufficient_data`.
- `knownSubtotal` может быть показан только как частичный subtotal.
- `finalTotal = null` для partial-варианта.
- UI, ссылка и PDF обязаны явно показать "недостаточно данных" для missing blocks.

`unusable`:

- Нет минимальной основы для skeleton estimate, либо отсутствуют snapshots/formula compatibility.
- Engine не должен придумывать строки.
- Допустимо вернуть только диагностические `warnings`, `riskFlags`, `missingBlocks` и audit step блокировки.
- Policy layer должен рассматривать это как `reject_as_incomplete` или `requires_review` по fail-closed правилам.

Минимальная основа для потолочного skeleton estimate:

- известна вертикаль и тип помещения;
- есть положительная площадь или доменное правило, позволяющее запросить площадь;
- есть совместимые formula manifest, price book snapshot, coefficient snapshot и pricing profile;
- валюта snapshots едина;
- нет противоречий, делающих расчет недостоверным, например отрицательная площадь.

## 6. Golden Estimate Fixture Format

Golden fixtures хранятся как YAML или JSON с canonical JSON-хэшами. Для денежных проверок tolerance равен нулю.

```yaml
contractVersion: calculation-engine.golden-fixture.v1
id: GE-001
title: simple-room-12sqm-no-light
source: expert
vertical: ceiling
calculationDate: "2026-05-23"
input:
  normalizedParams:
    region: moscow_region
    city: moscow
    roomType: bedroom
    areaSqm: "12.0"
    shape: rectangle
    fabricType: pvc
    fabricBrand: standard_brand
    cornersCount: 4
    heightM: "2.70"
    spotLightsCount: 0
    chandelierCount: 0
  formulaVersion: ceiling.v1
snapshots:
  priceBookSnapshotRef: fixtures/price-books/ceiling-basic-v1.json
  coefficientSnapshotRef: fixtures/coefficients/ceiling-basic-v1.json
  tenantPricingProfileSnapshotRef: fixtures/pricing-profiles/default-v1.json
  markupPolicySnapshotRef: fixtures/markup-policies/default-v1.json
expected:
  completenessStatus: complete
  missingBlocks: []
  variants:
    economy:
      status: complete
      finalTotal:
        amountMinor: "1800000"
        currency: RUB
    standard:
      status: complete
      finalTotal:
        amountMinor: "2250000"
        currency: RUB
    premium:
      status: complete
      finalTotal:
        amountMinor: "3180000"
        currency: RUB
  requiredAuditRules:
    - ceiling.v1.area
    - ceiling.v1.materials
    - ceiling.v1.work
    - ceiling.v1.variants
assertions:
  variantOrder: economy_lt_standard_lt_premium
  deterministicRuns: 100
  noFloatMoney: true
notes: "Synthetic engineering oracle. Not a real pilot price."
```

Partial fixture must assert:

- `completenessStatus = partial`;
- at least one `CalculationItem.calculationStatus = insufficient_data`;
- `finalTotal = null` for affected variants;
- missing block is visible as `"недостаточно данных"`.

Unusable fixture must assert:

- `completenessStatus = unusable`;
- no calculated amount-bearing lines;
- blocking reason is present in `riskFlags` or `warnings`.

## 7. Deterministic Tests

Minimum regression suite for `CalculationEngineV1`:

1. Same canonical `CalculationInput` returns byte-identical `resultHash` 100 times.
2. Same input with changed current system time returns the same result.
3. Same input with shuffled JSON object keys returns the same `inputHash` and result.
4. Engine does not read live price book after `PriceBookSnapshot` is supplied.
5. Old calculation snapshot remains unchanged after creating a newer price book version.
6. Money fields are integer minor units and never JS float.
7. Economy total is less than standard, standard is less than premium for approved full fixtures.
8. Fixed lines are not multiplied by complexity coefficients.
9. Work multiplier does not exceed the configured upper limit.
10. Missing required fields create `insufficient_data` lines or `unusable`, never invented prices.
11. Complex geometry without perimeter emits `requires_measurement` risk flag.
12. Partial result never exposes `finalTotal`.
13. Every calculated item has at least one audit step.
14. Audit step references immutable snapshot hashes.
15. Formula registry incompatibility returns `unusable` with blocking warning.
16. Rounding policy is applied only at configured `applyAt`.
17. Manual adjustments are absent from engine output; they belong to human review workflow.

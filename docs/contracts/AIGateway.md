# AIGateway.md

Дата: 2026-05-23  
Статус: контракт v1 для единого AI gateway  
Связано: `Scope.md`, `docs/Domain/DeterministicEstimation.md`, `docs/SolutionDesign.md`, `docs/Evals/QualityGates.md`

## 1. Назначение

AI gateway является единственным путем к LLM в ProSmet.

Gateway превращает пользовательский текст в безопасную структуру для дальнейшей нормализации: параметры, missing fields, уточняющие вопросы, assumptions, contradictions, risk flags и confidence.

Gateway не считает деньги, не видит прайсы, не получает денежные суммы и не принимает решение о публикации.

## 2. Safe Pipeline

```text
raw intake inside trusted server boundary
  -> consent/legal-basis check
  -> PII detection
  -> PII redaction
  -> money and price-field redaction
  -> prompt-injection and unsafe-instruction filtering
  -> safe structured provider payload
  -> provider call through gateway adapter
  -> output schema validation
  -> forbidden field rejection or stripping
  -> deterministic post-processing
  -> ai_payload_audit record
  -> safe AI result to application service
```

Запрещено отправлять provider adapter исходный текст, телефон, email, имя, адрес, файл, голос, прайс, коэффициенты, денежные суммы, PDF или расчетные строки.

## 3. Input Contracts

```ts
type ISODateTime = string;
type Hash = string;
type TenantId = string;
type LeadId = string;
type ConversationId = string;
type MessageId = string;
type JsonScalar = string | number | boolean | null;
type JsonValue = JsonScalar | JsonObject | JsonValue[];
type JsonObject = { [key: string]: JsonValue };
type DecimalString = string;

type AIGatewayPurpose =
  | "collect_params"
  | "normalize_params"
  | "clarify_missing_fields"
  | "classify_risk_flags"
  | "explain_calculated_estimate_without_money";

type AIGatewayRequest = {
  contractVersion: "ai-gateway.v1";
  tenantId: TenantId; // server-side context only
  leadId?: LeadId;
  conversationId?: ConversationId;
  messageIds: MessageId[];
  purpose: AIGatewayPurpose;
  locale: "ru-RU";
  channel: "owner_dashboard" | "widget" | "avito_entry" | "telegram" | "max" | "api";
  legalBasis: {
    consentAccepted: boolean;
    consentRecordId?: string;
    legalDocumentVersion?: string;
  };
  rawInputRef: {
    storage: "message.content_encrypted" | "transient_memory";
    contentHash: Hash;
  };
  rawTextForLocalRedaction: string;
  knownSafeParams?: JsonObject;
  allowedOutputSchemaId: "ceiling.estimate-draft-params.v1";
  providerPolicy: {
    allowProviderCall: boolean;
    fallbackOnProviderError: true;
    maxTokens?: number;
  };
};

type SafeProviderPayload = {
  contractVersion: "ai-provider-payload.v1";
  purpose: AIGatewayPurpose;
  sanitizedText: string;
  knownSafeParams?: JsonObject;
  allowedFields: string[];
  forbiddenFields: ForbiddenAIField[];
  instructions: {
    noPrices: true;
    noDiscounts: true;
    noCoefficientValues: true;
    noFinalTotals: true;
    askClarifyingQuestionWhenMissing: true;
  };
};
```

`rawTextForLocalRedaction` существует только внутри trusted server boundary. Он не логируется и не отправляется provider adapter.

## 4. Output Contract

```ts
type AIGatewayResult = {
  contractVersion: "ai-gateway.v1";
  status:
    | "ok"
    | "needs_clarification"
    | "blocked_by_consent"
    | "blocked_by_redaction"
    | "fallback_used"
    | "provider_failed";
  tenantId: TenantId;
  leadId?: LeadId;
  purpose: AIGatewayPurpose;
  normalizedParams: EstimateDraftParams;
  missingFields: string[];
  clarificationQuestions: ClarificationQuestion[];
  assumptions: string[];
  contradictions: string[];
  riskFlags: AIRiskFlag[];
  confidence: DecimalString | null; // 0.0000..1.0000, null if fallback cannot score
  explanationText?: string; // no money, no price, no final offer language
  redaction: RedactionSummary;
  auditRef: {
    aiPayloadAuditId: string;
    sanitizedPayloadHash: Hash;
    outputHash: Hash;
  };
};

type EstimateDraftParams = {
  region?: string;
  city?: string;
  roomType?: string;
  areaSqm?: DecimalString;
  shape?: string;
  fabricType?: string;
  fabricBrand?: string;
  colorOrPrint?: string;
  cornersCount?: number;
  heightM?: DecimalString;
  spotLightsCount?: number;
  chandelierCount?: number;
  perimeterM?: DecimalString;
  internalCornersCount?: number;
  externalCornersCount?: number;
  pipesCount?: number;
  hiddenCorniceM?: DecimalString;
  floatingContourM?: DecimalString;
  nichesCount?: number;
  levelsCount?: number;
  furniture?: string;
  floor?: number;
  hasElevator?: boolean;
  urgency?: "normal" | "urgent" | "unknown";
  floodingHistory?: boolean;
};

type ClarificationQuestion = {
  field: string;
  question: string;
  reason: "required_for_calculation" | "resolves_contradiction" | "reduces_measurement_risk";
};

type AIRiskFlag = {
  code: string;
  category: "requires_review" | "requires_measurement" | "blocks_ai_output";
  reason: string;
};

type RedactionSummary = {
  piiDetected: boolean;
  moneyDetected: boolean;
  forbiddenFieldsDetected: ForbiddenAIField[];
  replacements: {
    phone: number;
    email: number;
    name: number;
    address: number;
    money: number;
    priceField: number;
    fileOrVoice: number;
  };
};
```

## 5. Forbidden Fields

Forbidden AI input and output fields:

```ts
type ForbiddenAIField =
  | "phone"
  | "email"
  | "name"
  | "address"
  | "rawContact"
  | "voice"
  | "file"
  | "price"
  | "priceRub"
  | "unitPrice"
  | "priceBook"
  | "priceBookSnapshot"
  | "coefficient"
  | "coefficientValue"
  | "discount"
  | "margin"
  | "markup"
  | "estimateLineAmount"
  | "amount"
  | "subtotal"
  | "total"
  | "finalPrice"
  | "pdfAsset"
  | "clientLinkToken";
```

Output validator behavior:

- Если provider вернул forbidden field, поле удаляется из structured result.
- Если forbidden field влияет на смысл ответа, весь AI result получает `status = "blocked_by_redaction"`.
- `forbiddenFieldsDetected` сохраняется в audit без исходных значений.
- Сервисный слой не имеет права использовать удаленные forbidden values.

## 6. Redaction Rules

PII redaction:

- phone -> `[PHONE_REDACTED]`;
- email -> `[EMAIL_REDACTED]`;
- person name from structured contact field -> `[NAME_REDACTED]`;
- address, apartment, exact location -> `[ADDRESS_REDACTED]`;
- voice/file references -> `[FILE_REDACTED]`.

Money redaction:

- numeric amount with currency marker -> `[MONEY_REDACTED]`;
- phrases like "за 50000", "скидка 10%", "дешевле на 5 тыс" -> `[MONEY_REDACTED]`;
- any field named as forbidden price field -> `[PRICE_FIELD_REDACTED]`.

Prompt-injection handling:

- instructions to reveal prompt, ignore rules, calculate price, invent discount or bypass policy are removed from provider payload;
- the event is reflected as risk flag `prompt_injection_attempt`;
- gateway may still return safe missing fields or clarification questions.

## 7. AI Does Not Calculate

Provider payload must not contain:

- `PriceBookSnapshot`;
- `CoefficientSnapshot`;
- `TenantPricingProfileSnapshot`;
- `MarkupPolicySnapshot`;
- calculation item amounts;
- PDF content with prices;
- client link token;
- real phone, name, email, address;
- monetary amounts from client text.

AI result may contain:

- normalized non-money params;
- missing fields;
- assumptions;
- contradictions;
- risk flags;
- confidence;
- clarification questions;
- explanation of an already calculated estimate only if the source text contains no money.

AI result must not contain:

- prices;
- totals;
- discounts;
- coefficient values;
- estimate line amounts;
- auto-publish decision.

## 8. Audit Payload Contract

```ts
type AIPayloadAuditRecord = {
  contractVersion: "ai-payload-audit.v1";
  aiPayloadAuditId: string;
  tenantId: TenantId;
  leadId?: LeadId;
  conversationId?: ConversationId;
  purpose: AIGatewayPurpose;
  provider: "openai" | "none_fallback" | "test_double";
  model: string | null;
  status:
    | "ok"
    | "blocked_by_consent"
    | "blocked_by_redaction"
    | "fallback_used"
    | "provider_failed"
    | "schema_rejected";
  inputHash: Hash;
  sanitizedPayloadHash: Hash | null;
  providerOutputHash: Hash | null;
  safeOutputHash: Hash | null;
  piiDetected: boolean;
  moneyDetected: boolean;
  forbiddenFieldsDetected: ForbiddenAIField[];
  redactionSummary: RedactionSummary;
  fallbackUsed: boolean;
  errorClass?: "consent_missing" | "redaction_failed" | "provider_error" | "schema_validation_error";
  createdAt: ISODateTime;
};
```

Audit record stores hashes and counters, not raw PII, not raw money and not provider prompt text containing sensitive data.

## 9. Fallback Without LLM

Fallback is mandatory when:

- consent is missing for a flow that would inspect PII;
- provider call is disabled by environment or tenant policy;
- provider fails or times out;
- redaction cannot produce safe payload;
- output schema validation fails.

Fallback behavior:

- uses deterministic form answers and simple local parsers only;
- returns `knownSafeParams` as normalized params when possible;
- emits missing fields from the domain required-field list;
- emits clarification questions from static templates;
- sets `confidence = null` or conservative low value;
- never creates price, discount, coefficient or policy decision;
- writes `fallback_used` audit record.

## 10. Eval Corpus Categories

Minimum AI gateway eval corpus:

1. Clean complete ceiling request without PII and without money.
2. Missing required fields, AI must ask clarification.
3. Contradictory input, for example "4 угла" and "сложная форма 10 углов".
4. Phone, email, name and address in free text.
5. Money in free text, discount request and "сделайте дешевле".
6. Prompt injection asking AI to calculate price or ignore rules.
7. Avito-style noisy text with irrelevant listing fragments.
8. Commercial object and large area risk.
9. Complex geometry without perimeter.
10. Height above supported threshold.
11. More than 20 spotlights.
12. Fabric with flooding history.
13. Hidden cornice, floating contour or light lines without length.
14. Provider output contains forbidden price fields.
15. Provider timeout, fallback must return safe result.
16. Explanation request for calculated estimate, output must contain no money.

Passing gate:

- no provider payload contains PII or money;
- no safe output contains forbidden fields;
- missing fields and risk flags are preserved for policy layer;
- every call creates an audit record.


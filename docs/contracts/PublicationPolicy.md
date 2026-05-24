# PublicationPolicy.md

Дата: 2026-05-23  
Статус: контракт v1 для approval policy и publication workflow  
Связано: `docs/ADR/ADR-008-approval-policy-protocol.md`, `docs/ADR/ADR-014-partial-estimate-and-phone-gated-reveal.md`, `docs/SolutionDesign.md`, `docs/Evals/QualityGates.md`

## 1. Назначение

Publication policy определяет, можно ли раскрыть клиенту уникальную смету, создать клиентскую ссылку и PDF.

Решение принимает deterministic policy layer. Он получает immutable calculation snapshot и признаки readiness, legal, phone-gate, confidence, completeness и risk flags. Он не считает цены, не вызывает LLM и не меняет расчет.

## 2. ApprovalPolicyInput

```ts
type ISODateTime = string;
type Hash = string;
type TenantId = string;
type LeadId = string;
type CalculationId = string;
type PolicyProfileId = string;
type LegalPackVersion = string;

type ApprovalPolicyInput = {
  contractVersion: "publication-policy.v1";
  tenantId: TenantId; // server-side context only
  leadId: LeadId;
  calculationId: CalculationId;
  calculationSnapshot: {
    exists: boolean;
    immutable: boolean;
    snapshotHash: Hash | null;
    formulaVersion: string | null;
    priceBookVersion: string | null;
    priceBookHash: Hash | null;
    coefficientSnapshotHash: Hash | null;
    inputHash: Hash | null;
    createdAt: ISODateTime | null;
  };
  policyProfile: {
    policyProfileId: PolicyProfileId;
    policyVersion: string;
    autonomousOfferEnabled: boolean;
    minAiConfidence: string; // decimal string 0.0000..1.0000
    minCompletenessForFullPublish: string;
    minCompletenessForPartialPublish: string;
    allowPartialAutoPublish: boolean;
    blockingRiskFlags: string[];
    measurementRiskFlags: string[];
    requiresReviewRiskFlags: string[];
  };
  requiredFields: {
    name: string;
    present: boolean;
  }[];
  completeness: {
    status: "complete" | "partial" | "unusable";
    score: string; // decimal string 0.0000..1.0000
    missingBlocks: string[];
    insufficientDataVisibleToClient: boolean;
  };
  ai: {
    confidence: string | null;
    riskFlags: string[];
    missingFields: string[];
    contradictions: string[];
    payloadAuditId?: string;
  };
  calculationRiskFlags: string[];
  consent: {
    accepted: boolean;
    consentRecordId?: string;
    legalDocumentVersion: string | null;
  };
  phoneGate: {
    enabled: boolean;
    phoneCollected: boolean;
  };
  tenantReadiness: {
    priceBookReady: boolean;
    pricingProfileReady: boolean;
    formulaReady: boolean;
    legalPackReady: boolean;
    notificationChannelReady: boolean;
    clientLinkSigningReady: boolean;
    pdfRendererReady: boolean;
  };
  legalPack: {
    version: LegalPackVersion | null;
    containsPublicOfferDisclaimer: boolean;
  };
  manualAdjustments: {
    exists: boolean;
    approvedByHumanReview: boolean;
  };
  requestedPublication: {
    createClientLink: boolean;
    createPdf: boolean;
  };
};
```

Policy input intentionally does not include line item amounts, final totals, price items or coefficients. The policy checks whether a snapshot can be published, not how much it costs.

## 3. ApprovalPolicyDecision

```ts
type PublicationMode = "full" | "partial";

type ApprovalPolicyDecision =
  | {
      contractVersion: "publication-policy.v1";
      decisionId: string;
      decision: "auto_publish";
      publicationMode: PublicationMode;
      publishable: true;
      reasonCodes: ReasonCode[];
      policyVersion: string;
      policyProfileId: PolicyProfileId;
      inputHash: Hash;
      calculationId: CalculationId;
      calculationSnapshotHash: Hash;
      legalPackVersion: LegalPackVersion;
      decidedAt: ISODateTime;
    }
  | {
      contractVersion: "publication-policy.v1";
      decisionId: string;
      decision: "requires_review" | "requires_measurement" | "reject_as_incomplete";
      publicationMode: null;
      publishable: false;
      reasonCodes: ReasonCode[];
      policyVersion: string;
      policyProfileId: PolicyProfileId;
      inputHash: Hash;
      calculationId: CalculationId;
      calculationSnapshotHash: Hash | null;
      legalPackVersion: LegalPackVersion | null;
      decidedAt: ISODateTime;
    };
```

`publicationMode = "full"`:

- calculation completeness is `complete`;
- all amount-bearing blocks are calculated;
- client link/PDF may show full unique estimate after gates.

`publicationMode = "partial"`:

- calculation completeness is `partial`;
- tenant policy allows partial auto-publish;
- missing blocks are explicitly visible as "недостаточно данных";
- partial subtotal is not presented as final full price.

## 4. Reason Codes

```ts
type ReasonCode =
  | "AUTO_PUBLISH_FULL_ALLOWED"
  | "AUTO_PUBLISH_PARTIAL_ALLOWED"
  | "CALCULATION_SNAPSHOT_MISSING"
  | "CALCULATION_SNAPSHOT_MUTABLE"
  | "CALCULATION_UNUSABLE"
  | "CONSENT_MISSING"
  | "PHONE_GATE_REQUIRED"
  | "AUTONOMOUS_MODE_DISABLED"
  | "PRICE_BOOK_NOT_READY"
  | "PRICING_PROFILE_NOT_READY"
  | "FORMULA_NOT_READY"
  | "LEGAL_PACK_NOT_READY"
  | "LEGAL_DISCLAIMER_MISSING"
  | "NOTIFICATION_CHANNEL_NOT_READY"
  | "CLIENT_LINK_SIGNING_NOT_READY"
  | "PDF_RENDERER_NOT_READY"
  | "AI_CONFIDENCE_MISSING"
  | "AI_CONFIDENCE_LOW"
  | "AI_CONTRADICTION_PRESENT"
  | "AI_RISK_REQUIRES_REVIEW"
  | "AI_RISK_REQUIRES_MEASUREMENT"
  | "CALCULATION_RISK_REQUIRES_REVIEW"
  | "CALCULATION_RISK_REQUIRES_MEASUREMENT"
  | "MANUAL_ADJUSTMENT_PRESENT"
  | "MANUAL_ADJUSTMENT_NOT_REVIEWED"
  | "COMPLETENESS_BELOW_FULL_THRESHOLD"
  | "COMPLETENESS_BELOW_PARTIAL_THRESHOLD"
  | "PARTIAL_PUBLICATION_DISABLED"
  | "PARTIAL_VISIBILITY_NOT_GUARANTEED"
  | "MISSING_REQUIRED_FIELDS"
  | "LINK_GATE_BLOCKED"
  | "PDF_GATE_BLOCKED"
  | "POLICY_ERROR_FAIL_CLOSED";
```

Decision mapping:

- Missing or mutable snapshot -> `requires_review`.
- `unusable` calculation -> `reject_as_incomplete`.
- Missing consent -> `reject_as_incomplete`.
- Phone-gate enabled without phone -> no full publication; decision is `requires_review` for full reveal and preview may remain available.
- Autonomous mode disabled -> `requires_review`.
- Readiness gaps -> `requires_review`.
- Measurement risk flags -> `requires_measurement`.
- Contradictions, manual adjustments, review risk flags -> `requires_review`.
- AI confidence below threshold -> `requires_review`.
- Complete, clean, ready input -> `auto_publish` with `publicationMode = "full"`.
- Partial, clean, ready input with visible missing blocks and tenant allowance -> `auto_publish` with `publicationMode = "partial"`.

## 5. Publication State Machine

```ts
type PublicationState =
  | "draft"
  | "preview_available"
  | "awaiting_phone"
  | "calculation_snapshotted"
  | "policy_decided"
  | "requires_review"
  | "requires_measurement"
  | "rejected_as_incomplete"
  | "human_approved"
  | "auto_publish_authorized"
  | "client_link_created"
  | "pdf_queued"
  | "pdf_ready"
  | "published_to_client"
  | "expired"
  | "revoked"
  | "failed_closed";
```

Allowed transitions:

```text
draft -> preview_available
preview_available -> awaiting_phone
awaiting_phone -> calculation_snapshotted
preview_available -> calculation_snapshotted, if phone-gate disabled
calculation_snapshotted -> policy_decided
policy_decided -> requires_review
policy_decided -> requires_measurement
policy_decided -> rejected_as_incomplete
policy_decided -> auto_publish_authorized
requires_review -> human_approved
human_approved -> client_link_created
auto_publish_authorized -> client_link_created
client_link_created -> pdf_queued
pdf_queued -> pdf_ready
client_link_created -> published_to_client, if PDF is not required before reveal
pdf_ready -> published_to_client
published_to_client -> expired
published_to_client -> revoked
any non-terminal state -> failed_closed on policy/link/PDF gate error
```

Terminal states:

- `published_to_client`;
- `expired`;
- `revoked`;
- `rejected_as_incomplete`;
- `failed_closed`.

## 6. Fail-Closed Behavior

Fail-closed rules:

- Policy exception produces `requires_review` with `POLICY_ERROR_FAIL_CLOSED`, unless input is clearly `unusable`, then `reject_as_incomplete`.
- Link or PDF gate failure must not reveal full estimate.
- If audit write fails, publication artifact is not created.
- If phone-gate state is unknown and tenant has phone-gate enabled, full reveal is blocked.
- If legal pack or disclaimer state is unknown, publication is blocked.
- If `publicationMode = "partial"` and UI/PDF cannot show missing blocks, publication is blocked.
- If idempotency conflict is detected, service returns existing audited artifact or blocks for review.

## 7. Link and PDF Gates

Client link may be created only when one source is true:

- `human_reviews.decision = approve`; or
- `approval_policy_decisions.decision = auto_publish`.

```ts
type PublicationArtifactGateInput = {
  tenantId: TenantId;
  leadId: LeadId;
  calculationId: CalculationId;
  calculationSnapshotHash: Hash;
  source:
    | { kind: "human_review"; reviewId: string; approved: true }
    | { kind: "policy_decision"; decisionId: string; decision: "auto_publish"; publicationMode: PublicationMode };
  phoneGate: {
    enabled: boolean;
    phoneCollected: boolean;
  };
  legalPack: {
    version: LegalPackVersion;
    containsPublicOfferDisclaimer: true;
  };
  artifactRequest: {
    createClientLink: boolean;
    createPdf: boolean;
    pdfRequiredBeforeReveal: boolean;
  };
};

type PublicationArtifactGateDecision = {
  allowed: boolean;
  reasonCodes: ReasonCode[];
  publicationMode: PublicationMode | null;
};
```

Client link requirements:

- raw token is shown only once to caller and never stored;
- DB stores `token_hash`;
- link token does not expose tenant id, lead id or calculation id;
- link is bound to tenant, lead, calculation and publication source;
- link opening uses signed token or hashed lookup under tenant-safe context;
- expired token reveals no estimate details.

PDF requirements:

- PDF is rendered from immutable calculation snapshot;
- PDF includes calculation version, formula version, price book version and validity date;
- PDF includes legal phrase: "не является публичной офертой (ст. 437 ГК РФ). Окончательные условия определяются в договоре по результатам замера.";
- PDF for partial publication shows every missing block as "недостаточно данных";
- PDF is created only after human approval or audited `auto_publish`;
- PDF download writes analytics event.

## 8. Audit Events

```ts
type PublicationAuditEvent =
  | "approval_policy_decision_created"
  | "approval_policy_failed_closed"
  | "human_review_approved"
  | "human_review_requested_changes"
  | "human_review_required_measurement"
  | "client_link_created"
  | "client_link_creation_blocked"
  | "pdf_generation_queued"
  | "pdf_generation_failed"
  | "pdf_asset_created"
  | "published_to_client"
  | "auto_published_to_client"
  | "publication_revoked"
  | "publication_expired"
  | "preview_shown"
  | "phone_submitted"
  | "opened"
  | "reopened"
  | "pdf_downloaded"
  | "cta_clicked"
  | "expired_link_opened";

type PublicationAuditPayload = {
  contractVersion: "publication-audit.v1";
  tenantId: TenantId;
  leadId: LeadId;
  calculationId?: CalculationId;
  eventType: PublicationAuditEvent;
  actorType: "system" | "user" | "client_session" | "worker";
  actorIdHash?: Hash;
  entityType:
    | "approval_policy_decision"
    | "human_review"
    | "client_estimate_link"
    | "pdf_asset"
    | "client_link_event"
    | "publication_workflow";
  entityId: string;
  idempotencyKey?: string;
  payloadHash: Hash;
  occurredAt: ISODateTime;
};
```

Audit payload must not include raw phone, name, email, address, raw link token, unredacted IP, user-agent or AI provider payload.

Client analytics events:

- `preview_shown` before phone may record blurred/partial preview only.
- `phone_submitted` records completion of phone-gate.
- `opened` records first client link opening.
- `reopened` records repeat opening or counter update with audit.
- `pdf_downloaded` records PDF download.
- `cta_clicked` records next-step click.
- `expired_link_opened` records expired access without reveal.

## 9. Required Tests

Minimum tests for publication policy:

1. `auto_publish` is impossible without immutable calculation snapshot.
2. Missing consent blocks publication.
3. Phone-gate enabled without phone blocks full reveal.
4. Autonomous mode disabled returns `requires_review`.
5. Readiness gaps return `requires_review`.
6. Measurement risk flag returns `requires_measurement`.
7. Review risk flag, contradiction or manual adjustment returns `requires_review`.
8. Low AI confidence returns `requires_review`.
9. Complete clean calculation returns `auto_publish` with `publicationMode = "full"`.
10. Partial clean calculation returns `auto_publish` with `publicationMode = "partial"` only when tenant allows it and missing blocks are visible.
11. Partial visibility failure blocks publication.
12. Unusable calculation returns `reject_as_incomplete`.
13. Policy exception produces fail-closed decision and audit event.
14. Link creation is allowed only after human approval or audited `auto_publish`.
15. PDF contains formula version, price book version and legal phrase.
16. Client events write idempotent audit/analytics records.


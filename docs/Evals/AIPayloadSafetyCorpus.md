# AI Payload Safety Corpus

Дата: 2026-05-23
Статус: synthetic eval corpus для AI gateway

## Назначение

Корпус фиксирует oracle для redaction, forbidden output fields and fallback behavior. Он нужен до подключения любого реального provider adapter.

Файл:

```text
fixtures/ai-gateway/ai-payload-safety-cases.json
```

## Инварианты

- Raw input может содержать synthetic PII and money examples.
- Expected provider payload не содержит phone, name, email, address, money, price book, PDF or final totals.
- Forbidden output fields must be rejected: `price`, `priceRub`, `finalPrice`, `discount`, `margin`, `coefficientValue`, `estimateLineAmount`, `total`.
- If redaction fails, gateway fails closed and asks safe clarification or returns `needs_human_review`.

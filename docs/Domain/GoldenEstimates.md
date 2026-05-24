# Golden Estimates

Дата: 2026-05-23
Статус: synthetic engineering oracle перед реализацией engine

## Назначение

Golden estimates нужны не для реального пилотного прайса, а для воспроизводимой разработки calculation engine. Они фиксируют ожидаемые результаты на synthetic stub price book.

Реальный прайс пилота остается отдельным решением архитектора и не попадает в repo без разрешения.

## Fixtures

Файлы:

```text
fixtures/price-books/ceiling-basic-v1.json
fixtures/coefficients/ceiling-basic-v1.json
fixtures/pricing-profiles/default-v1.json
fixtures/markup-policies/default-v1.json
fixtures/golden-estimates/*.json
```

Каждый golden fixture:

- использует `contractVersion = golden-estimate.v1`;
- ссылается на immutable synthetic snapshots;
- имеет expected status, totals или partial semantics;
- имеет `assertions.deterministicRuns = 100`;
- имеет нулевой tolerance для денег;
- явно помечен как `synthetic_stub`.

## Stub Formula For Fixtures

Эти fixtures задают oracle для первой реализации `ceiling.v1`:

```text
materials = areaSqm * fabricUnitPrice
  + perimeterM * profileUnitPrice
  + fixedRoomMaterial
  + spotLightsCount * spotlightMaterial
  + chandelierCount * chandelierMaterial

work = areaSqm * baseWorkRate * complexityMultiplier
  + perimeterM * profileInstallWork
  + fixedRoomWork
  + spotLightsCount * spotlightWork
  + chandelierCount * chandelierWork

knownSubtotal = materials + work
finalTotal = max(rounded(knownSubtotal), minimumOrderAmount)
```

`complexityMultiplier` for current fixtures:

```text
1.00
+ 0.03 for every corner above 4
+ 0.12 if heightM > 3.00
+ 0.20 if urgency = urgent
```

Rounding uses synthetic profile `nearest_100_rub` with direction `up`.

## Важное ограничение

SeniorCeilingEstimator может проверять fixtures как development oracle, но runtime-клиенту цену создает только deterministic calculation engine.

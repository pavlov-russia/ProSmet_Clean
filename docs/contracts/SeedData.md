# SeedData Contract

Дата: 2026-05-23
Статус: synthetic seed contract for local verification

## Назначение

Seed data нужен, чтобы BackendDeveloper и QAEngineer проверяли tenant isolation, consent, PII audit, signed links and publication gates на одинаковых данных.

Файл:

```text
fixtures/seeds/tenant-ab.json
```

## Правила

- Только synthetic/test данные.
- Никаких реальных телефонов, email, адресов, имен клиентов или пилотных прайсов.
- Tenant A и Tenant B должны иметь похожие сущности, чтобы тест ловил cross-tenant leakage.
- Любой original PII placeholder должен быть явно помечен как synthetic.
- Link tokens в seed не являются реальными: хранится только token hash.

## Минимальное покрытие

- два tenant;
- два owner user;
- memberships;
- consent records;
- leads and rooms;
- calculation snapshots;
- client links;
- link events;
- `pii_access_log`;
- audit events.

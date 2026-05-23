# Backlogs.md

Дата: 2026-05-19

## Product Backlog

- Собрать 5-10 golden estimates от эксперта или пилота.
- Уточнить первый пилот и источник реального прайса.
- Уточнить phone-gate: всегда ли телефон обязателен перед выдачей сметы или зависит от tenant.
- Зафиксировать первый клиентский выход: уникальная ссылка + PDF как обязательный комплект или ссылка с PDF по кнопке.
- Описать минимальный вход из Авито: ссылка, QR, промежуточная страница, UTM/source.
- Выбрать первый чат-канал владельца: Telegram, Max или оба.
- Уточнить минимальный legal pack для клиентской формы.
- Определить список risk flags для `auto_publish`.
- Определить порог AI confidence для autonomous offer mode.
- Проверить, нужен ли голос до первого автономного текстового пилота.

## Architecture Backlog

- Описать полную модель данных в `docs/SolutionDesign.md`.
- Описать API контракты MVP.
- Описать расчетный graph и формульный registry.
- Описать RLS policy matrix.
- Описать AI gateway schemas.
- Описать PDF/link generation pipeline.
- Описать approval policy engine и `approval_policy_decisions`.
- Описать client link analytics: open, reopen, pdf_downloaded, cta_clicked.
- Доработать ADR-003/ADR-007 в связке human review vs autonomous offer mode.

## Engineering Backlog

- Scaffold монорепо.
- Настроить strict TypeScript.
- Настроить Drizzle и миграции.
- Реализовать `withTenant`.
- Реализовать calculation engine как pure module.
- Реализовать regression tests на golden estimates.
- Реализовать AI payload audit.
- Реализовать unique client links и event tracking.
- Реализовать approval policy service.
- Реализовать owner web notifications и первый bot adapter.

## Documentation Backlog

- Утвердить `Vision.md`.
- Утвердить `Scope.md`.
- Собрать `ConceptualDesign.md`.
- Собрать `SolutionDesign.md`.
- Добавить PlantUML/Mermaid схемы компонентов.
- Создать расширенные role cards для AI-сотрудников разработки, включая senior AI-сметчика.
- Подготовить PDF-render pipeline для Solution Design.

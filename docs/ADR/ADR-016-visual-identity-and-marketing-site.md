# ADR-016 · Visual identity and ProSmet marketing site

Дата: 2026-05-24  
Статус: принято  
Связано: `Scope.md`, `docs/SolutionDesign.md`, `docs/Architecture.md`, `docs/contracts/VisualIdentityAndMarketingSite.md`, `docs/Context/2026-05-24-visual-and-marketing-site-input.md`

## Контекст

Из материалов `docs/Visual` приняты новые вводные:

- ProSmet должен выглядеть легко: много воздуха, светлый фон, бело-голубая основа and мягкие фиолетовые акценты.
- Интерфейс владельца должен быть единым рабочим окном, а не тяжелой CRM.
- Mobile-first важен для владельца, мастера и менеджера.
- Нужен отдельный сайт ProSmet для рекламы нашего сервиса потолочным компаниям.

В текущем Scope уже есть сайт/виджет подрядчика как B2C entry и отложенная генерация сайтов подрядчиков. Но public website самого ProSmet как marketing/acquisition surface не был явно отделен от tenant runtime.

## Решение

Добавляем отдельный pre-launch public marketing surface:

```text
apps/marketing
  -> ProSmet public marketing site
  -> home / potolki landing / demo request / privacy / legal
  -> shared visual tokens from packages/ui
  -> synthetic screenshots and public marketing copy
  -> no tenant/customer runtime data
```

Фиксируем visual identity contract:

```text
docs/contracts/VisualIdentityAndMarketingSite.md
```

Стартовая палитра:

- white/light-blue base;
- blue primary actions;
- violet AI/status accents;
- calm dashboard surfaces;
- mobile-first single-window UX.

## Границы

Marketing site может:

- объяснять ценность ProSmet;
- показывать synthetic screenshots and demo data;
- собирать demo/pilot request after consent;
- писать неперсональные marketing events.

Marketing site не может:

- читать tenant/customer data;
- показывать реальные ПД, реальные сметы, реальные прайсы or pilot screenshots без отдельного approval;
- отправлять contact data в LLM;
- обещать точные цены, скидки, ROI or legal guarantees without contract/legal review;
- включать production deploy or external analytics provider без ArchitectInterventionRequest.

## Последствия

- `apps/marketing` становится отдельным приложением в архитектуре, но не блокирует calculation MVP path.
- `TASK-012A/B/C` добавлены как draft work package for ProductAnalyst, FrontendDeveloper and QAEngineer.
- Implementation может стартовать только после закрытия базовых dependencies and explicit readiness decision.
- Генерация сайтов подрядчиков остается отложенной частью платформы и не смешивается с сайтом ProSmet.


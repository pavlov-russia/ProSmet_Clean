# Visual Identity and Marketing Site Contract

Дата: 2026-05-24  
Статус: архитектурный контракт для визуального направления и pre-launch сайта ProSmet

## 1. Назначение

Этот контракт фиксирует базовый UX/UI-направление ProSmet и отдельный public marketing site для рекламы сервиса потолочным компаниям.

Он не меняет расчетное ядро, AI safety boundaries, tenant isolation, publication policy or Scope стартовой вертикали.

Контракт применяется ко всем интерфейсам ProSmet с первого frontend-среза:

- public marketing site;
- клиентский widget/form;
- Avito entry;
- owner dashboard;
- admin/settings screens;
- human review UI;
- client estimate link;
- PDF/link visual templates where applicable.

Нельзя сначала собрать админку или кабинет в произвольном стиле, а потом "натянуть бренд". `packages/ui` and visual tokens являются foundation для всех frontend tasks.

## 2. Визуальные принципы

- Много воздуха: интерфейс не должен выглядеть как тяжелая CRM.
- Светлая основа: белый и светло-голубой фон.
- Акценты: голубой для основного действия, мягкий фиолетовый для AI/status accents.
- Строгая типографика: без декоративных шрифтов, плотная читаемость для dashboard.
- Единое рабочее окно: заявки, чаты, AI-выводы, статусы и next action рядом.
- Mobile-first: владелец/мастер может работать с телефона.
- Быстрые действия: нижнее меню на мобильном, явные primary CTA, короткие формы.
- Гибридный ввод: чат, quick replies and classic forms coexist.

## 3. Initial Design Tokens

Палитра фиксируется как стартовая и может уточняться после первого UI-прототипа.

```text
background:        #F7FBFF
surface:           #FFFFFF
surface-muted:     #EEF7FF
border:            #D8E8F6
text-primary:      #111827
text-secondary:    #64748B
primary-blue:      #4EA7E8
primary-blue-dark: #1F7FC1
accent-violet:     #A78BFA
accent-violet-2:   #C4B5FD
success:           #22C55E
warning:           #F59E0B
danger:            #EF4444
```

Правила применения:

- основной интерфейс не должен становиться одноцветно-голубым или фиолетовым;
- голубой используется для главного действия and navigation active state;
- фиолетовый используется точечно: AI insights, helper hints, secondary accents;
- warning/danger используются только для настоящих рисков, errors, blockers;
- карточки, таблицы и панели в dashboard остаются спокойными и сканируемыми.

## 4. Marketing Site

`apps/marketing` — публичный сайт ProSmet для рекламы нашего сервиса.

Назначение:

- объяснить ProSmet простым языком потолочным компаниям и мастерам;
- показать, что это не тяжелая CRM, а быстрый расчетно-сметный контур;
- привести к заявке на demo/pilot;
- собрать первичные маркетинговые события and leads без доступа к tenant data.

Минимальные страницы:

- `/` — главный оффер ProSmet;
- `/potolki` — страница стартовой вертикали натяжных потолков;
- `/demo` — форма заявки на demo/pilot;
- `/privacy` — политика обработки данных для marketing lead;
- `/terms` или `/legal` — базовые юридические условия/дисклеймеры.

Минимальные блоки:

- H1 с названием `ProSmet`;
- понятный one-liner: платформа умных смет для потолочных компаний;
- проблема: заявки теряются, сметы считаются вручную, клиент ждет;
- решение: виджет/чат -> расчет -> ссылка/PDF -> лиды и аналитика;
- демонстрация продукта на synthetic UI/screens, без реальных ПД;
- CTA: "Запросить демо" / "Обсудить пилот";
- блок доверия: deterministic calculation, human review, no AI pricing;
- legal/disclaimer: маркетинговые обещания не являются публичной офертой.

## 5. Boundaries

Marketing site может:

- использовать публичные материалы ProSmet;
- показывать synthetic screenshots and demo data;
- собирать consented demo request;
- писать marketing analytics events;
- использовать shared UI tokens from `packages/ui`.

Marketing site не может:

- читать tenant/customer tables напрямую;
- показывать реальные сметы, прайсы, ПД or pilot data without explicit approval;
- передавать phone/email/name в LLM;
- обещать точную цену, скидку, ROI or legal guarantees;
- отправлять данные во внешние сервисы без ArchitectInterventionRequest;
- включать production deploy без отдельного решения архитектора.

## 6. Data and API Boundary

Маркетинговый lead отделен от tenant lead.

Минимальные сущности будущей реализации:

- `marketing_leads`;
- `marketing_events`;
- `marketing_consent_records`.

Минимальные события:

- `marketing.page_viewed`;
- `marketing.hero_cta_clicked`;
- `marketing.demo_requested`;
- `marketing.vertical_interest_clicked`.

Минимальный API:

- `POST /api/marketing/leads` — создать заявку на demo/pilot after consent;
- `POST /api/marketing/events` — записать неперсональное событие сайта.

## 7. AI Build Team Ownership

- `ProductAnalyst`: message, audience, conversion metrics, UX acceptance.
- `FrontendDeveloper`: visual tokens, responsive marketing pages, UI implementation.
- `BusinessAnalyst`: legal/consent wording.
- `SolutionArchitect`: API/data boundaries.
- `QAEngineer`: browser smoke, no real PII/prices in fixtures/screens.
- `PPM`: task cards and sequencing.

## 8. Acceptance

- Visual tokens are documented before UI implementation.
- Marketing site is separate from tenant/customer runtime data.
- Lead form has consent before phone/email/name.
- Synthetic screenshots/data are visibly not pilot data.
- No production deploy, external analytics provider or real PII flow is added without architect approval.

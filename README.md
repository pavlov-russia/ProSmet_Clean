# ProSmet Clean

Дата сборки: 2026-05-19  
Статус: чистовой архитектурный пакет на основе черновика `ProjectProSmet`

## Назначение

Эта папка отделяет чистовую архитектуру ProSmet от черновых слоев проекта.

Здесь зафиксированы:

- harness для AI-агентов: `AGENTS.md`, `CLAUDE.md`, `.claude/settings.json`, `Team.yml`;
- единое продуктовое видение без MVP-ограничений: `Vision.md`;
- жесткие рамки реализации MVP: `Scope.md`;
- методологический слой AI_M_MSF: `docs/AI_M_MSF.md`;
- концептуальное решение: `docs/ConceptualDesign.md`;
- техническое решение: `docs/SolutionDesign.md`;
- архитектурные детали: `docs/Architecture.md`;
- методология формирования harness: `docs/HarnessMethodology.md`;
- предметная модель и детерминированный расчет: `docs/Domain/`;
- проверки качества и рисков: `docs/Evals/QualityGates.md`;
- источники и методологические основания: `docs/Sources.md`.

## Канон проекта

1. Стартовая вертикаль: натяжные потолки.
2. Первый доказуемый путь: сайт/Авито -> согласие -> чатовый сбор параметров -> preview сметы -> телефон -> детерминированный расчет -> уникальная клиентская ссылка и PDF -> метрики -> статус сделки.
3. AI собирает, нормализует, проверяет пропуски и объясняет. Деньги считает расчетное ядро.
4. Персональные данные и денежные суммы не отправляются в LLM.
5. Мультитенантность и RLS проектируются с первого дня.
6. MVP считается завершенным только после autonomous offer mode для типовых заявок: без ручного действия компании после настройки tenant.
7. Human review остается режимом калибровки и обработки исключений: сложная геометрия, низкий confidence, ручная скидка, юридический риск, необходимость замера.
8. Интерфейс владельца строится как web-кабинет плюс Telegram и/или Max-бот для уведомлений и быстрых действий.
9. Внешние черновые источники больше не являются рабочей опорой clean-пакета.

## Структура

```text
ProSmet_Clean/
  AGENTS.md                  # Общий harness для AI-агентов
  CLAUDE.md                  # Адаптер Claude Code, импортирует AGENTS.md
  Team.yml                   # AI-команда разработки проекта
  Focus.md                   # Текущий фокус
  Backlogs.md                # Бэклог
  EntryPointForTask.md       # Как стартовать новую задачу
  Vision.md                  # Long Vision + MVP Vision без ограничений
  Scope.md                   # Жесткие рамки MVP
  docs/
    AI_M_MSF.md              # Методология Vision / Scope / Conceptual / Solution
    ConceptualDesign.md      # Концептуальное представление решения
    SolutionDesign.md        # Логическая схема компонентов и протоколов
    Architecture.md          # Техническая архитектура и инварианты
    HarnessMethodology.md    # Как создавать AGENTS.md / CLAUDE.md / Scope / Vision
    Sources.md               # Что было изучено и как использовано
    ADR/                     # Архитектурные решения
    Domain/                  # Предметная модель и расчетное ядро
    Evals/                   # Проверки и quality gates
    Context/                 # Принятые контекстные правки и handoff для новых чатов
  harness/
    build-team.md            # AI-сотрудники, которые собирают проект
    agent-roles.md           # Рабочие роли AI-команды и минимальные runtime AI-функции MVP
    scripts/README.md        # Место для проектных проверочных скриптов
    skills/README.md         # Место для проектных skills
  tasks/
    task_template.yml        # Шаблон handoff-задачи для AI-сотрудника
  reports/
    README.md                # Отчеты сотрудников
  workspace/
    README.md                # Рабочая зона временных артефактов
  .claude/
    settings.json            # Реальные разрешения/запреты Claude Code
    agents/README.md         # Место для subagents
    rules/README.md          # Место для path-scoped rules
  .codex/
    agents/README.md         # Место для agent profiles
```

## Порядок работы

1. Любая продуктовая задача сверяется с `Vision.md` и `Scope.md`.
2. Для текущей итерации дополнительно читается `docs/Context/2026-05-19-autonomous-mvp-feedback.md`.
3. Любая концептуальная задача сверяется с `docs/ConceptualDesign.md`.
4. Любая техническая задача сверяется с `docs/SolutionDesign.md` и `docs/Architecture.md`.
5. Любой расчетный или AI-контур обязан пройти проверки из `docs/Evals/QualityGates.md`.
6. Новое архитектурное решение фиксируется в `docs/ADR/`.
7. Если задача расширяет MVP, сначала обновляется `Scope.md`, потом код.

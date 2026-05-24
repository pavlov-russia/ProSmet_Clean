# AI Product Build Team Template

Статус: переносимый шаблон AI-команды для разработки новых продуктов  
Основа: опыт ProSmet, но без привязки к натяжным потолкам

## Что это

Это папка-шаблон, которую можно положить в новый проект и сказать AI:

```text
Используй этот шаблон как рабочий harness для проекта.
Сначала подготовь Vision, Scope, Conceptual Design, Solution Design,
затем разбей работу на маленькие задачи с evidence.
```

Шаблон нужен, чтобы AI-команда работала не хаотично, а по понятному процессу:

```text
идея -> Vision -> Scope -> Conceptual Design -> Solution Design -> ADR -> task cards -> implementation -> evidence
```

## Как использовать в новом чате

1. Скопируй эту папку в новый проект.
2. Открой новый чат.
3. Вставь текст из `NEW_CHAT_PROMPT.md`.
4. Дай AI описание нового продукта.
5. Попроси сначала подготовить архитектуру, а не сразу код.

## Что внутри

- `NEW_CHAT_PROMPT.md` — готовый prompt для нового чата.
- `AGENTS.template.md` — правила работы AI-команды.
- `Team.template.yml` — универсальная команда AI-сотрудников.
- `docs/AI_M_MSF.md` — методология документов.
- `docs/ArchitecturePreparationGuide.md` — пошаговая подготовка архитектуры.
- `docs/RoleCatalog.md` — кто за что отвечает.
- `docs/TaskAndEvidenceProtocol.md` — как ставить задачи и принимать работу.
- `docs/QualityGatesTemplate.md` — шаблон проверок качества.
- `tasks/task_template.yml` — шаблон задачи.
- `docs/contracts/` — шаблоны отчетов и запросов к архитектору.

## Универсальные сотрудники

В шаблоне есть роли, которые подходят почти для любого продукта:

- AIOrchestrator
- Architect
- ProductAnalyst
- BusinessAnalyst
- DomainAnalyst
- DomainExpert
- SolutionArchitect
- RulesEngineDeveloper
- BackendDeveloper
- FrontendDeveloper
- AIFlowDeveloper
- QAEngineer
- DevOps
- PPM

## Что нужно заменить под новый проект

В каждом новом проекте обязательно заменить:

- название продукта;
- целевую аудиторию;
- предметную область;
- DomainExpert;
- правила качества;
- юридические ограничения;
- источники реальных данных;
- список функций MVP.

Пример:

```text
ProSmet:
DomainExpert = SeniorCeilingEstimator
RulesEngineDeveloper = EstimationEngineDeveloper

Юридический продукт:
DomainExpert = LegalExpert
RulesEngineDeveloper = DocumentRulesDeveloper

Медицинский продукт:
DomainExpert = MedicalExpert
RulesEngineDeveloper = ClinicalRulesDeveloper
```

## Главное правило

AI-команда не должна начинать код без:

- Vision;
- Scope;
- архитектурных границ;
- task cards;
- quality gates;
- evidence protocol.


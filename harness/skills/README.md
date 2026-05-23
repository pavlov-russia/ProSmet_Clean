# harness/skills

Здесь должны жить локальные skills проекта ProSmet.

Кандидаты:

- `prosmet-scope-guardian` — проверяет, не расширяет ли задача MVP.
- `prosmet-domain-analyst` — помогает собирать golden estimates и предметные параметры.
- `prosmet-estimation-evaluator` — проверяет расчетные кейсы и edge cases.
- `prosmet-ai-safety-reviewer` — проверяет AI gateway, PII и money redaction.
- `prosmet-conceptual-design-builder` — собирает Conceptual Design из Vision и Scope.
- `prosmet-solution-design-builder` — собирает Solution Design из Conceptual Design и архитектурных решений.

Правило:

- skill должен быть узким;
- skill должен иметь входы, выходы, запреты и критерий завершения;
- skill не заменяет `Scope.md` и ADR.

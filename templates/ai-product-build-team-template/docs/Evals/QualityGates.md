# QualityGates.md

Стартовые gates для нового проекта. Адаптируй под продукт.

## Architecture Gates

- `ARCH.INTAKE.READY`: есть первичный Vision/Scope draft and open decisions.
- `ARCH.CONTRACT.ALIGNMENT`: Vision, Scope, Conceptual Design, Solution Design and Architecture do not conflict.
- `ARCH.ADR.REQUIRED`: новое архитектурное решение имеет ADR.

## AI Gates

- AI не получает ПД, секреты or forbidden sensitive data.
- AI output проверяется схемой там, где влияет на продукт.
- AI не является источником истины для денег, права, медицины, безопасности or critical decisions.

## Evidence Gates

- Каждая task имеет evidence report.
- `passed` нельзя ставить без реально выполненной проверки.
- `not_run` всегда имеет reason.


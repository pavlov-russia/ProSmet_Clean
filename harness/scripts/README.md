# harness/scripts

Здесь должны жить проектные проверочные скрипты.

Планируемые скрипты:

- `check-core-boundary` — проверяет, что `packages/core` не содержит потолочных терминов.
- `check-ai-payload-fixtures` — проверяет fixtures на отсутствие ПД и денежных сумм.
- `check-pdf-legal` — проверяет обязательную юридическую фразу в PDF/link templates.
- `check-tenant-access` — запускает cross-tenant regression tests.

Правило:

- агент не должен ссылаться на скрипт как на существующий, пока файл реально не создан.
- новый скрипт должен иметь README или usage внутри файла.
- скрипты не читают `.env` и не требуют production secrets.

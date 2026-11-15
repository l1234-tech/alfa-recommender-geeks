# Каталог «Альфа-Курса»

Храните предоставленный архив и любые выгрузки локально. Файлы данных в этой
папке игнорируются Git. При запуске без архива API использует демо-каталог.

Обычный `.sql` или `.sql.gz` в этой папке восстанавливается при первом запуске
PostgreSQL с пустым Docker volume.

## Восстановление предоставленного `.backup`

Выполните команды из корня проекта. В базе `alfa_course` не должно быть ранее
восстановленных таблиц. Для отдельной проверки с новым volume добавьте
`-p alfa-db-check` после `docker compose` во всех командах и укажите свободные
порты по [README](../README.md).

Нужен `pg_restore` версии 17 или новее, доступный в PATH. Замените
`/path/to/alfa_course_hackathon.backup` на путь к своему файлу.

```bash
docker compose up -d --wait db
(
  set -e
  set -o pipefail
  archive=/path/to/alfa_course_hackathon.backup
  restore_sql=$(mktemp)
  trap 'rm -f "$restore_sql"' EXIT
  pg_restore --no-owner --no-privileges --file=- "$archive" |
    sed '1,30{/^SET transaction_timeout = 0;$/d;}' > "$restore_sql"
  docker compose exec -T db psql -X -U alfa -d alfa_course \
    --set=ON_ERROR_STOP=1 --single-transaction --file=- < "$restore_sql"
)
```

Строка `SET transaction_timeout` удаляется из заголовка SQL для совместимости с
PostgreSQL 16. `psql` запускается внутри сервиса `db`, поэтому подключается к
нужной базе даже при наличии PostgreSQL на компьютере.

После успешного восстановления запустите стек. Если Backend уже был запущен,
перезапустите его, чтобы сбросить кэш каталога.

```bash
docker compose up -d --build --wait
docker compose restart backend
docker compose up -d --wait
```

Проверьте API одним запросом:

```bash
curl -fsS http://localhost:8000/api/v1/recommendations \
  -H 'Content-Type: application/json' -d '{"limit":1}'
```

При загрузке из PostgreSQL в `metadata.catalog_source` будет `database`.
Значение `sample` означает демо-каталог.

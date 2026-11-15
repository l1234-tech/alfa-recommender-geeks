# data/ — provided dataset (NOT committed)

The private Альфа-Курс dataset is **never** committed to git. This folder is
mounted into the `db` service at `/docker-entrypoint-initdb.d`, so a plain SQL
dump placed here is restored automatically on the **first** `docker compose up`.

## How to use

1. Put the provided PostgreSQL dump here as a single `.sql` file, e.g.:

   ```
   data/alfa_course_dump.sql
   ```

2. Start the stack from the repo root:

   ```bash
   docker compose up --build
   ```

   The `db` service restores the dump, then `backend` loads the catalog from it
   via the ML loader (`recommender/data_processing/catalog.sql`).

3. Existing volumes are preserved. To import a different dump, create a separate database or a new named volume and restore there; do not remove the existing volume. Custom dumps need pg_restore with a matching PostgreSQL version. Never commit the dump.

## Notes

- Only `*.sql` / `*.sql.gz` / `*.sh` files run on init. This `README.md` is ignored.
- If the dump is in PostgreSQL **custom** format (`pg_dump -Fc`, `.dump`/`.backup`),
  it won't auto-restore — restore it manually with `pg_restore` into the `db`
  service, or convert it to plain SQL.
- No dump present → the DB is empty and the backend falls back to its demo
  catalog, so the service still runs.

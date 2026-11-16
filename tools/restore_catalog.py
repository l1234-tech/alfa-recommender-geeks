"""Restore the supplied plain SQL dump into the Compose PostgreSQL database."""
from __future__ import annotations
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dump", nargs="?", default=str(ROOT / "data" / "alfa_course_hackathon.sql"))
    dump = Path(parser.parse_args().dump).expanduser().resolve()
    if not dump.is_file():
        print(f"SQL dump not found: {dump}", file=sys.stderr)
        return 2
    check = subprocess.run(
        ["docker", "compose", "exec", "-T", "db", "psql", "-X", "-U", "alfa",
         "-d", "alfa_course", "-Atqc",
         "SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE'"],
        cwd=ROOT, text=True, capture_output=True,
    )
    if check.returncode:
        print(check.stderr or check.stdout, file=sys.stderr)
        print("Start PostgreSQL first: docker compose up -d --wait db", file=sys.stderr)
        return check.returncode
    if check.stdout.strip() != "0":
        print("Database is not empty; refusing to overwrite. Reset only a disposable local volume with docker compose down -v.", file=sys.stderr)
        return 3
    command = ["docker", "compose", "exec", "-T", "db", "psql", "-X", "-v",
               "ON_ERROR_STOP=1", "-1", "-U", "alfa", "-d", "alfa_course"]
    process = subprocess.Popen(command, cwd=ROOT, stdin=subprocess.PIPE, text=True, encoding="utf-8")
    assert process.stdin is not None
    try:
        with dump.open("r", encoding="utf-8") as source:
            for line in source:
                if line.startswith("\\restrict ") or line.startswith("\\unrestrict "):
                    continue
                if line.strip() == "SET transaction_timeout = 0;":
                    continue
                process.stdin.write(line)
        process.stdin.close()
    except (BrokenPipeError, OSError, UnicodeError) as exc:
        process.kill()
        print(f"Could not stream SQL dump: {exc}", file=sys.stderr)
        return 4
    result = process.wait()
    if result:
        print("Restore failed; transaction was rolled back.", file=sys.stderr)
        return result
    print("Catalog SQL dump restored successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

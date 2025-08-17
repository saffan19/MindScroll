import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT"))

ROOT = Path(__file__).resolve().parents[1]
schema_path = ROOT / "sql" / "schema.sql"
indices_path = ROOT / "sql" / "indices.sql"


def run_sql(cursor, path, split_statements=False):
    """Execute SQL file. By default, execute whole script."""
    with open(path, "r", encoding="utf-8") as f:
        sql = f.read()
        if split_statements:
            for stmt in sql.split(";"):
                stmt = stmt.strip()
                if stmt:
                    cursor.execute(stmt + ";")
        else:
            cursor.execute(sql)


def ensure_database():
    """Check if database exists; create if missing."""
    conn = psycopg2.connect(
        dbname="postgres",
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
    exists = cur.fetchone()

    if not exists:
        print(f"Database '{DB_NAME}' does not exist. Creating it...")
        cur.execute(f"CREATE DATABASE {DB_NAME};")
    else:
        print(f"Database '{DB_NAME}' already exists.")

    cur.close()
    conn.close()


def ensure_extensions(cur):
    """Safely create required extensions if missing."""
    extensions = ["pg_trgm", "vector"]
    for ext in extensions:
        cur.execute(f"""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = '{ext}') THEN
                CREATE EXTENSION {ext};
            END IF;
        END$$;
        """)


def main():
    ensure_database()
    conn = psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
    )
    conn.autocommit = True
    cur = conn.cursor()

    print("Dropping all tables (keep extensions intact)...")
    # Drop only tables, not the schema
    cur.execute("""
        DO $$
        DECLARE
            r RECORD;
        BEGIN
            FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
            END LOOP;
        END $$;
    """)

    print("Enabling required extensions ...")
    cur.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")  # must exist before tables

    print("Applying schema.sql ...")
    run_sql(cur, schema_path, split_statements=False)  # run whole schema at once

    print("Applying indices.sql ...")
    run_sql(cur, indices_path, split_statements=False)

    cur.close()
    conn.close()
    print("Schema and indices initialized successfully.")




if __name__ == "__main__":
    main()

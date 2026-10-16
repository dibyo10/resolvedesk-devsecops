import time

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .db import engine


def wait_for_migration(database, expected, attempts=120, interval=2):
    for attempt in range(attempts):
        try:
            with database.connect() as connection:
                actual = connection.execute(
                    text("SELECT version_num FROM alembic_version")
                ).scalar()
                if actual == expected:
                    return
        except SQLAlchemyError:
            pass
        if attempt + 1 < attempts:
            time.sleep(interval)
    raise RuntimeError("Database migration did not become ready")


def main():
    expected = ScriptDirectory.from_config(Config("alembic.ini")).get_current_head()
    try:
        wait_for_migration(engine, expected)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()

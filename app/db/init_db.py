from sqlalchemy import text

from app.db.schema import CREATE_TABLES_SQL
from app.db.session import engine


def init_db() -> None:
    with engine.begin() as conn:
        for statement in CREATE_TABLES_SQL:
            conn.execute(text(statement))


if __name__ == "__main__":
    init_db()
    print("Database schema initialized successfully.")
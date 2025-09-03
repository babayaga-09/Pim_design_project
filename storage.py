import sqlite3
from typing import Optional
from pim_types import Particle, ParticleId


def make_connection(db_path: str = "pim.db") -> sqlite3.Connection:
    """
    Open (or create) a SQLite database and ensure tables exist.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # dict-like row access
    _create_tables(conn)
    return conn


def _create_tables(conn: sqlite3.Connection) -> None:
    """Create required tables if they don't exist."""
    cur = conn.cursor()

    # Users
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password_hash TEXT NOT NULL
    )
    """)

    # Sessions
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        token TEXT PRIMARY KEY,
        username TEXT NOT NULL,
        FOREIGN KEY (username) REFERENCES users(username)
    )
    """)

    # Particles
    cur.execute("""
    CREATE TABLE IF NOT EXISTS particles (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        body TEXT NOT NULL,
        tags TEXT,
        created_at TEXT,
        updated_at TEXT,
        author TEXT
    )
    """)

    conn.commit()



def save_particle(conn: sqlite3.Connection, p: Particle) -> None:
    """
    Insert or replace a particle in the database.
    Tags are stored as a comma-separated string.
    """
    cur = conn.cursor()
    cur.execute("""
    INSERT OR REPLACE INTO particles (id, title, body, tags, created_at, updated_at, author)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        p.id, p.title, p.body, ",".join(p.tags),
        p.created_at, p.updated_at, p.author
    ))
    conn.commit()


def delete_particle(conn: sqlite3.Connection, pid: ParticleId) -> bool:
    """Delete a particle by id. Return True if deleted."""
    cur = conn.cursor()
    cur.execute("DELETE FROM particles WHERE id = ?", (pid,))
    conn.commit()
    return cur.rowcount > 0


def get_particle(conn: sqlite3.Connection, pid: ParticleId) -> Optional[Particle]:
    """Fetch a particle by id. Return None if not found."""
    cur = conn.cursor()
    cur.execute("SELECT * FROM particles WHERE id = ?", (pid,))
    row = cur.fetchone()
    if not row:
        return None
    return Particle(
        id=row["id"],
        title=row["title"],
        body=row["body"],
        author=row["author"],
        tags=set(row["tags"].split(",")) if row["tags"] else set(),
        created_at=row["created_at"],
        updated_at=row["updated_at"]
    )


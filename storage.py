"""
This module handles all direct interactions with the SQLite database.
It includes functions for creating the database schema and performing CRUD
(Create, Read, Update, Delete) operations on particles.
"""

import sqlite3
from typing import Optional, List
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
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash BLOB NOT NULL
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        token TEXT PRIMARY KEY,
        username TEXT NOT NULL,
        FOREIGN KEY (username) REFERENCES users(username)
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS particles (
        id TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        user_facing_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        body TEXT NOT NULL,
        tags TEXT,
        created_at TEXT,
        updated_at TEXT,
        author TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id),
        UNIQUE(author, user_facing_id)
    )
    """)
    conn.commit()



def save_particle(conn: sqlite3.Connection, p: Particle):
    """Insert or update a particle."""
    tags_str = ",".join(sorted(list(p.tags)))
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO particles (id, user_id, user_facing_id, title, body, tags, created_at, updated_at, author)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            title=excluded.title,
            body=excluded.body,
            tags=excluded.tags,
            updated_at=excluded.updated_at
    """, (p.id, p.user_id, p.user_facing_id, p.title, p.body, tags_str, p.created_at, p.updated_at, p.author))

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
        user_id=row["user_id"],
        user_facing_id=row["user_facing_id"],
        title=row["title"],
        body=row["body"],
        author=row["author"],
        tags=set(row["tags"].split(",")) if row["tags"] else set(),
        created_at=row["created_at"],
        updated_at=row["updated_at"]
    )


def get_particle_by_user_id(conn: sqlite3.Connection, author: str, user_id: int) -> Optional[Particle]:
    """Fetch a particle by its user-facing ID and author."""
    cur = conn.cursor()
    cur.execute("SELECT * FROM particles WHERE author = ? AND user_id = ?", (author, user_id))
    row = cur.fetchone()
    if not row:
        return None
    return Particle(
        id=row["id"],
        user_id=row["user_id"],
        user_facing_id=row["user_facing_id"],
        title=row["title"],
        body=row["body"],
        author=row["author"],
        tags=set(row["tags"].split(",")) if row["tags"] else set(),
        created_at=row["created_at"],
        updated_at=row["updated_at"]
    )

def get_all_particles_by_author(conn: sqlite3.Connection, author: str) -> List[Particle]:
    """Fetch all particles for a given author, ordered by most recent."""
    cur = conn.cursor()
    cur.execute("SELECT * FROM particles WHERE author = ? ORDER BY created_at DESC", (author,))

    particles = []
    for row in cur.fetchall():
        particles.append(Particle(
            id=row["id"],
            user_id=row["user_id"],
            user_facing_id=row["user_facing_id"],
            title=row["title"],
            body=row["body"],
            author=row["author"],
            tags=set(row["tags"].split(",")) if row["tags"] else set(),
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        ))
    return particles



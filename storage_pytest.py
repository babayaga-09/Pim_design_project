import pytest
import sqlite3
from typing import Set
from datetime import datetime

from storage import make_connection, save_particle, get_particle, delete_particle
from pim_types import Particle

@pytest.fixture
def conn():
    # Use in-memory DB; make_connection creates tables automatically.
    c = make_connection(":memory:")
    try:
        yield c
    finally:
        c.close()

def _p(**overrides) -> Particle:
    base = dict(
        id="p1",
        title="Hello",
        body="World",
        author="alice",
        tags={"note", "pim"},  # Set order shouldn't matter
        created_at="2025-09-01T10:00:00Z",
        updated_at="2025-09-01T10:00:00Z",
    )
    base.update(overrides)
    return Particle(**base)

def test_tables_exist(conn):
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    names = {r[0] for r in cur.fetchall()}
    assert {"users", "sessions", "particles"} <= names

def test_insert_and_get_particle_round_trip(conn):
    p = _p()
    save_particle(conn, p)
    got = get_particle(conn, p.id)
    assert got is not None
    assert got.id == p.id
    assert got.title == p.title
    assert got.body == p.body
    assert got.author == p.author
    assert isinstance(got.tags, set)
    assert got.tags == p.tags
    assert got.created_at == p.created_at
    assert got.updated_at == p.updated_at

def test_get_particle_not_found_returns_none(conn):
    assert get_particle(conn, "nope") is None

def test_insert_or_replace_updates_existing_row(conn):
    first = _p(id="p2", title="First Title", updated_at="2025-09-01T10:00:00Z")
    save_particle(conn, first)

    # Replace same id with new data
    second = _p(id="p2", title="Second Title",
                body="Changed", tags={"x", "y"},
                updated_at="2025-09-02T11:00:00Z")
    save_particle(conn, second)

    got = get_particle(conn, "p2")
    assert got is not None
    assert got.title == "Second Title"
    assert got.body == "Changed"
    assert got.tags == {"x", "y"}
    assert got.updated_at == "2025-09-02T11:00:00Z"

def test_delete_particle_success_and_idempotency(conn):
    p = _p(id="p3")
    save_particle(conn, p)

    # First delete should succeed
    assert delete_particle(conn, "p3") is True
    # Row is gone
    assert get_particle(conn, "p3") is None
    # Deleting again should report False
    assert delete_particle(conn, "p3") is False

def test_tags_handle_empty_and_none_safely(conn):
    # Save with empty set of tags
    p_empty = _p(id="p4", tags=set())
    save_particle(conn, p_empty)
    got_empty = get_particle(conn, "p4")
    assert got_empty is not None
    assert got_empty.tags == set()

    # Manually insert a NULL tags row to ensure robustness
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO particles (id, title, body, tags, created_at, updated_at, author) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("p5", "T", "B", None, "c", "u", "a"),
    )
    conn.commit()
    got_null = get_particle(conn, "p5")
    assert got_null is not None
    assert got_null.tags == set()

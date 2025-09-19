import pytest
import sqlite3
import storage  # We need it to create the tables
from search import parse_query, query

# Fixture to set up a database populated with specific test data 

@pytest.fixture
def populated_db():
    """
    Provides an in-memory database connection pre-loaded with a variety
    of particles to test different search scenarios.
    """
    conn = storage.make_connection(":memory:")
    cur = conn.cursor()

    # Create users first to satisfy foreign key constraints
    cur.execute("INSERT INTO users (id, username, password_hash) VALUES (?, ?, ?)", (1, "testuser", "hash"))
    cur.execute("INSERT INTO users (id, username, password_hash) VALUES (?, ?, ?)", (2, "anotheruser", "hash"))

    # Create particle data for 'testuser'
    particles_data = [
        # id, user_id, user_facing_id, title, body, author
        ("p1", 1, 101, "A Quick Brown Fox", "The fox is a clever animal.", "testuser"),
        ("p2", 1, 102, "The Lazy Dog", "A story about a dog who loves sleeping.", "testuser"),
        ("p3", 1, 103, "Advanced Python Search", "Searching is a key skill in Python.", "testuser"),
        ("p4", 1, 104, "Another Clever Story", "This story is about a clever fox.", "testuser"),
        # Particle for another user that should NOT be found
        ("p5", 2, 201, "Secrets of Another User", "This particle contains python but belongs to someone else.", "anotheruser"),
    ]

    for pid, uid, ufid, title, body, author in particles_data:
        cur.execute(
            """
            INSERT INTO particles (id, user_id, user_facing_id, title, body, author, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """,
            (pid, uid, ufid, title, body, author)
        )
    conn.commit()
    yield conn
    conn.close()

# Tests for the _parse_query helper function 

def test_parse_query_keywords():
    """Tests parsing of simple, space-separated keywords."""
    keywords, phrases = parse_query("hello world")
    assert keywords == ["hello", "world"]
    assert phrases == []

def test_parse_query_phrase():
    """Tests parsing of a single exact phrase in double quotes."""
    keywords, phrases = parse_query('"exact phrase"')
    assert keywords == []
    assert phrases == ["exact phrase"]

def test_parse_query_mixed():
    """Tests parsing a mix of keywords and an exact phrase."""
    keywords, phrases = parse_query('keyword1 "an exact phrase" keyword2')
    assert keywords == ["keyword1", "keyword2"]
    assert phrases == ["an exact phrase"]

# Tests for the main query() function 

def test_query_empty_string(populated_db):
    """Tests that an empty query returns all particles for the user."""
    results = query(populated_db, "testuser", "")
    # Should return all 4 particles belonging to testuser
    assert len(results) == 4

def test_query_single_keyword_in_title(populated_db):
    """Tests finding a particle via a single keyword in its title."""
    results = query(populated_db, "testuser", "lazy")
    assert len(results) == 1
    assert results[0].id == "p2"

def test_query_single_keyword_in_body(populated_db):
    """Tests finding a particle via a single keyword in its body."""
    results = query(populated_db, "testuser", "sleeping")
    assert len(results) == 1
    assert results[0].id == "p2"

def test_query_and_logic_multiple_keywords(populated_db):
    """Tests that a query with multiple keywords requires all to be present (AND logic)."""
    results = query(populated_db, "testuser", "python search")
    assert len(results) == 1
    assert results[0].id == "p3"

def test_query_phrase_search(populated_db):
    """Tests an exact phrase search."""
    results = query(populated_db, "testuser", '"clever fox"')
    assert len(results) == 1
    assert results[0].id == "p4"

def test_query_author_isolation(populated_db):
    """Tests that a search for one user does not return results from another."""
    results = query(populated_db, "testuser", "python")
    assert len(results) == 1
    assert results[0].id == "p3", "Search should not find particles from other users."

def test_query_score_ordering(populated_db):
    """
    Tests that title matches are scored higher than body matches.
    'clever' is in the title of p1 and the body of p4.
    """
    results = query(populated_db, "testuser", "clever")
    assert len(results) == 2
    # p1 has "clever" in the title (score: 5), p4 has it in the body (score: 2)
    # The actual title is "A Quick Brown Fox", but body is "The fox is a clever animal."
    # The actual title of p4 is "Another Clever Story", body is "This story is about a clever fox."
    # Let's re-check the scoring. p4 has clever in title. p1 has clever in body.
    # Therefore, p4 should come first.
    assert results[0].id == "p4" # Higher score because "clever" is in the title
    assert results[1].id == "p1" # Lower score because "clever" is in the body

def test_query_no_results(populated_db):
    """Tests that a search for a non-existent term returns an empty list."""
    results = query(populated_db, "testuser", "nonexistentword")
    assert len(results) == 0

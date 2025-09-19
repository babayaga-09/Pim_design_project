import sqlite3
import pytest
from unittest.mock import MagicMock, patch
from edit_particles import (
    normalize_title,
    create_particle,
    update_particle_title,
    update_particle_body,
    add_tags,
    remove_tags,
    delete_particle
)
from authorise import User
from pim_types import Particle

# A pytest fixture to create a fresh in-memory database for each test
@pytest.fixture
def db_connection():
    """Provides an in-memory SQLite database connection for tests."""
    # Using ":memory:" creates a temporary database that exists only for the duration of the test
    conn = sqlite3.connect(":memory:")
    # We need to create the necessary tables for our tests to interact with
    conn.execute("""
        CREATE TABLE particles (
            id TEXT PRIMARY KEY,
            user_id INTEGER,
            user_facing_id INTEGER,
            title TEXT,
            body TEXT,
            tags TEXT,
            created_at TEXT,
            updated_at TEXT,
            author TEXT,
            UNIQUE(author, user_facing_id)
        );
    """)
    conn.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash BLOB NOT NULL
        );
    """)
    yield conn
    conn.close()

# Mock user for testing purposes
@pytest.fixture
def test_user():
    """Provides a mock User object, which is what the functions expect."""
    return User(id=1, username="testuser")

# A sample particle for use in update/delete tests
@pytest.fixture
def sample_particle(test_user):
    """Provides a mock Particle object for functions that need an existing particle."""
    return Particle(
        id="test-particle-id",
        user_id=test_user.id,
        user_facing_id=1,
        created_at="2023-01-01T12:00:00",
        updated_at="2023-01-01T12:00:00",
        title="Original Title",
        body="Original Body",
        tags={"testing", "python"},
        author=test_user.username,
    )

def test_normalize_title():
    """
    Tests that normalize_title converts to lowercase and strips extra whitespace.
    This is a pure function with no dependencies, so it's the simplest kind of test.
    """
    assert normalize_title("  My  Fancy   Title ") == "my fancy title"
    assert normalize_title("AnotherTitle") == "anothertitle"
    assert normalize_title("ALREADY NORMAL") == "already normal"


# We used @patch to "mock" functions from the `storage` module.
# This isolates our tests to ONLY the logic within `edit_particles.py`.
# We assumed the storage functions work; they have their own tests

@patch("storage.save_particle")
def test_create_particle_success(mock_save, db_connection, test_user):
    """
    Tests successful particle creation.
    Verifies that the function creates a particle with correct data and calls the storage layer.
    """
    title = "A New Note"
    body = "This is the content."
    tags = {"work", "important"}

    # Call the function with the mock User object
    particle = create_particle(db_connection, test_user, title, body, tags)

    # Assert that the returned particle object has the correct attributes
    assert particle.title == title
    assert particle.body == body
    assert particle.tags == tags
    assert particle.author == test_user.username
    assert particle.user_facing_id == 1
    # Assert that the mocked storage function was called exactly once
    mock_save.assert_called_once()

def test_create_particle_increments_user_facing_id(db_connection, test_user):
    """
    Tests that the user_facing_id correctly increments for a specific user.
    """
    # Arrange: Simulate a user already having a particle with a user_facing_id of 5
    db_connection.execute(
        "INSERT INTO particles (id, user_id, user_facing_id, title, body, author) VALUES (?, ?, ?, ?, ?, ?)",
        ("existing-id", test_user.id, 5, "Old Title", "Old Body", test_user.username)
    )
    db_connection.commit()

    # Act: Create a new particle for the same user
    with patch("storage.save_particle"):
         new_particle = create_particle(db_connection, test_user, "New Title", "New Body", set())
         # Assert: The new ID should be 6
         assert new_particle.user_facing_id == 6


def test_create_particle_empty_title_fails(db_connection, test_user):
    """
    Tests that creating a particle with an empty or whitespace title raises a ValueError.
    """
    with pytest.raises(ValueError, match="Title and body cannot be empty"):
        create_particle(db_connection, test_user, "  ", "Some body", {"tag"})

def test_create_particle_duplicate_title_fails(db_connection, test_user):
    """
    Tests that creating a particle with a duplicate title for the same user raises a ValueError.
    """
    # Arrange: Simulate an existing particle with a title that will cause a conflict
    db_connection.execute(
        "INSERT INTO particles (id, user_id, title, author) VALUES (?, ?, ?, ?)",
        ("some-id", test_user.id, "duplicate title", test_user.username)
    )
    db_connection.commit()
    # Act & Assert: Expect a ValueError when trying to create another particle with the same title
    with pytest.raises(ValueError, match="You already have a particle with this title"):
        create_particle(db_connection, test_user, "Duplicate Title", "Some body", set())


@patch("storage.get_particle")
@patch("storage.save_particle")
def test_update_particle_title_success(mock_save, mock_get, db_connection, test_user, sample_particle):
    """
    Tests that a particle's title can be successfully updated by its author.
    """
    # Arrange: Configure the mock to return our sample particle when called
    mock_get.return_value = sample_particle
    new_title = "An Updated Title"

    # Act: Call the function to update the title
    updated = update_particle_title(db_connection, test_user.username, sample_particle.id, new_title)

    # Assert: Check that the mocks were called and the particle was updated
    mock_get.assert_called_with(db_connection, sample_particle.id)
    mock_save.assert_called_once()
    assert updated.title == new_title
    assert updated.id == sample_particle.id
    assert updated.updated_at != sample_particle.updated_at

@patch("storage.get_particle")
def test_update_particle_title_permission_denied(mock_get, db_connection, sample_particle):
    """
    Tests that updating a particle's title by a different user raises PermissionError.
    """
    mock_get.return_value = sample_particle
    # Expect a PermissionError when a different user tries to update the title
    with pytest.raises(PermissionError, match="You do not have permission to modify this particle."):
        update_particle_title(db_connection, "anotheruser", sample_particle.id, "New Title")

@patch("storage.get_particle")
@patch("storage.save_particle")
def test_add_tags_success(mock_save, mock_get, db_connection, test_user, sample_particle):
    """
    Tests that new tags are correctly added to a particle's existing tags.
    """
    mock_get.return_value = sample_particle
    tags_to_add = {"newtag", "anothertag"}

    updated = add_tags(db_connection, test_user.username, sample_particle.id, tags_to_add)

    # The new set of tags should be a union of the old and new tags
    assert updated.tags == {"testing", "python", "newtag", "anothertag"}
    mock_save.assert_called_once()


@patch("storage.get_particle")
@patch("storage.save_particle")
def test_remove_tags_success(mock_save, mock_get, db_connection, test_user, sample_particle):
    """
    Tests that tags are correctly removed from a particle.
    """
    mock_get.return_value = sample_particle
    tags_to_remove = {"testing", "nonexistent"} # one existing tag, one not

    updated = remove_tags(db_connection, test_user.username, sample_particle.id, tags_to_remove)

    # The new set of tags should have the specified tags removed
    assert updated.tags == {"python"}
    mock_save.assert_called_once()

@patch("storage.get_particle")
@patch("storage.delete_particle")
def test_delete_particle_success(mock_delete, mock_get, db_connection, test_user, sample_particle):
    """
    Tests that a particle can be successfully deleted by its author.
    """
    mock_get.return_value = sample_particle
    mock_delete.return_value = True # Simulate a successful deletion in storage

    result = delete_particle(db_connection, test_user.username, sample_particle.id)
    assert result is True
    mock_delete.assert_called_with(db_connection, sample_particle.id)

@patch("storage.get_particle")
def test_delete_particle_permission_denied(mock_get, db_connection, sample_particle):
    """
    Tests that deleting a particle by another user raises a PermissionError.
    """
    mock_get.return_value = sample_particle
    with pytest.raises(PermissionError, match="You do not have permission to delete this particle."):
        delete_particle(db_connection, "anotheruser", sample_particle.id)


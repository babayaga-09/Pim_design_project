import sqlite3
import pytest
import storage
from pim_types import Particle

# This fixture sets up a clean database for each test
@pytest.fixture
def db_connection():
    """
    Provides an in-memory SQLite db connection where the actual tables have been created.
    """
    conn = storage.make_connection(":memory:")
    # We must add a user to satisfy the foreign key constraint on particles.user_id
    conn.execute(
        "INSERT INTO users (id, username, password_hash) VALUES (?, ?, ?)",
        (1, "testuser", "fake_hash")
    )
    conn.commit()
    yield conn
    conn.close()

# This fixture provides a sample particle object for testing
@pytest.fixture
def sample_particle():
    """Provides a reusable Particle object for tests."""
    return Particle(
        id="test-uuid-123",
        user_id=1,
        user_facing_id=101,
        title="Test Title",
        body="Test Body",
        author="testuser",
        tags={"tag1", "tag2"},
        created_at="2025-01-01T00:00:00",
        updated_at="2025-01-01T00:00:00",
    )

def test_save_and_get_particle(db_connection, sample_particle):
    """
    Tests that a particle can be saved and then retrieved with the exact same data.
    This is the most fundamental test for the storage layer.
    """
    # Act: Save the particle to the database
    storage.save_particle(db_connection, sample_particle)

    # Act: Retrieve the same particle by its ID
    retrieved = storage.get_particle(db_connection, sample_particle.id)

    # Assert: The retrieved particle should be identical to the one we saved
    assert retrieved is not None
    assert retrieved == sample_particle

def test_get_particle_not_found(db_connection):
    """
    Tests that getting a particle with a non-existent ID returns None.
    """
    retrieved = storage.get_particle(db_connection, "non-existent-id")
    assert retrieved is None

def test_save_particle_updates_existing(db_connection, sample_particle):
    """
    Tests that saving a particle with an existing ID updates the record.
    This verifies the "ON CONFLICT(id) DO UPDATE" part of the SQL query.
    """
    # Arrange: Save the initial version of the particle
    storage.save_particle(db_connection, sample_particle)

    # Act: Create a modified version of the particle with a new title and tags
    updated_particle = sample_particle._replace(
        title="Updated Title",
        tags={"updated_tag"}
    )
    # Save the modified particle (this should trigger an update, not an insert)
    storage.save_particle(db_connection, updated_particle)

    # Assert: Retrieve the particle and check that its data reflects the update
    retrieved = storage.get_particle(db_connection, sample_particle.id)
    assert retrieved is not None
    assert retrieved.title == "Updated Title"
    assert retrieved.tags == {"updated_tag"}
    assert retrieved.body == sample_particle.body # Body should be unchanged

def test_delete_particle(db_connection, sample_particle):
    """
    Tests that a particle can be successfully deleted.
    """
    # Arrange: Save a particle so that we can delete it
    storage.save_particle(db_connection, sample_particle)

    # Act: Delete the particle and check the return status
    was_deleted = storage.delete_particle(db_connection, sample_particle.id)
    assert was_deleted is True

    # Assert: The particle should no longer be in the database
    retrieved = storage.get_particle(db_connection, sample_particle.id)
    assert retrieved is None

def test_get_all_particles_by_author(db_connection, sample_particle):
    """
    Tests that all particles for a specific author are returned, and not from others.
    """
    # Arrange: Create several particles, some for the target author, some for another
    p1 = sample_particle._replace(id="p1", user_facing_id=201, created_at="2025-01-02T00:00:00")
    p2 = sample_particle._replace(id="p2", user_facing_id=202, created_at="2025-01-01T00:00:00") # Older

    # A particle from a different user
    db_connection.execute(
        "INSERT INTO users (id, username, password_hash) VALUES (?, ?, ?)",
        (2, "otheruser", "fake_hash")
    )
    other_user_particle = sample_particle._replace(id="p3", user_id=2, author="otheruser", user_facing_id=203)

    storage.save_particle(db_connection, p1)
    storage.save_particle(db_connection, p2)
    storage.save_particle(db_connection, other_user_particle)

    # Act: Retrieve all particles for the original 'testuser'
    all_user_particles = storage.get_all_particles_by_author(db_connection, "testuser")

    # Assert:
    # 1. We should get exactly 2 particles.
    assert len(all_user_particles) == 2
    # 2. They should be ordered by creation date, most recent first.
    assert all_user_particles[0].id == "p1"
    assert all_user_particles[1].id == "p2"
    # 3. The other user's particle should not be in the list.
    assert "p3" not in [p.id for p in all_user_particles]

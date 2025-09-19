import sqlite3
import pytest
from authorise import (
    _hash_password,
    _verify_password,
    register_user,
    login,
    logout,
    whoami,
    User,
)

# Fixture to provide a clean in-memory database for each test function
@pytest.fixture
def db_connection():
    """Provides an in-memory SQLite database connection with necessary tables."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row # Allows accessing columns by name
    # Create the tables required by the authorise module
    conn.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        );
    """)
    conn.execute("""
        CREATE TABLE sessions (
            token TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            FOREIGN KEY (username) REFERENCES users(username)
        );
    """)
    yield conn
    conn.close()

# Tests for Helper Functions 

def test_password_hashing_and_verification():
    """
    Tests that hashing a password and verifying it works,
    and that verification fails for an incorrect password.
    """
    password = "my_super_secret_password"
    hashed_password = _hash_password(password)

    # Assert that the original password verifies against the hash
    assert _verify_password(password, hashed_password) is True
    # Assert that an incorrect password does NOT verify
    assert _verify_password("wrong_password", hashed_password) is False
    # Assert that the hash is a string and not empty
    assert isinstance(hashed_password, str)
    assert hashed_password != ""

# Tests for Public API Functions

def test_register_user_success(db_connection):
    """
    Tests that a new user can be successfully registered.
    """
    result = register_user(db_connection, "newuser", "password123")
    assert result is True

    # Verify directly in the DB that the user was created
    cur = db_connection.cursor()
    cur.execute("SELECT username, password_hash FROM users WHERE username = ?", ("newuser",))
    user_row = cur.fetchone()
    assert user_row is not None
    assert user_row["username"] == "newuser"
    # Check that the stored password is a valid hash
    assert _verify_password("password123", user_row["password_hash"])

def test_register_user_duplicate_fails(db_connection):
    """
    Tests that registering a user with an existing username fails.
    """
    # Arrange: Register a user first
    register_user(db_connection, "existinguser", "password123")

    # Act & Assert: Attempting to register the same username should return False
    result = register_user(db_connection, "existinguser", "another_password")
    assert result is False

def test_login_success(db_connection):
    """
    Tests that a user can successfully log in with correct credentials.
    """
    # Arrange: Register a user to log in with
    username = "testuser"
    password = "password123"
    register_user(db_connection, username, password)

    # Act: Attempt to log in
    result = login(db_connection, username, password)

    # Assert: The result should be successful
    assert result.ok is True
    assert result.session is not None
    assert isinstance(result.session, str)

    # Verify that a session token was created in the database
    cur = db_connection.cursor()
    cur.execute("SELECT username FROM sessions WHERE token = ?", (result.session,))
    session_row = cur.fetchone()
    assert session_row is not None
    assert session_row["username"] == username

def test_login_wrong_password_fails(db_connection):
    """
    Tests that login fails when an incorrect password is provided.
    """
    username = "testuser"
    password = "password123"
    register_user(db_connection, username, password)

    result = login(db_connection, username, "wrong_password")

    assert result.ok is False
    assert result.session is None
    assert result.message == "Invalid password"

def test_login_nonexistent_user_fails(db_connection):
    """
    Tests that login fails when the username does not exist.
    """
    result = login(db_connection, "ghostuser", "any_password")

    assert result.ok is False
    assert result.session is None
    assert result.message == "User does not exist"

def test_whoami_success(db_connection):
    """
    Tests that whoami correctly identifies a user from a valid session token.
    """
    # Arrange: Register and log in a user to get a valid session token
    register_user(db_connection, "myuser", "password")
    login_result = login(db_connection, "myuser", "password")
    session_token = login_result.session

    # Act: Call whoami with the token
    user = whoami(db_connection, session_token)

    # Assert: The correct user object should be returned
    assert user is not None
    assert user.username == "myuser"
    assert isinstance(user.id, int)

def test_whoami_invalid_token_returns_none(db_connection):
    """
    Tests that whoami returns None for an invalid or non-existent session token.
    """
    user = whoami(db_connection, "invalid-token-string")
    assert user is None

def test_logout_success(db_connection):
    """
    Tests that logout successfully removes a session token from the database.
    """
    # Arrange: Register and log in to create a session
    register_user(db_connection, "myuser", "password")
    login_result = login(db_connection, "myuser", "password")
    session_token = login_result.session

    # Act: Log the user out
    result = logout(db_connection, session_token)
    assert result is True

    # Assert: The session should no longer be in the database
    user = whoami(db_connection, session_token)
    assert user is None

def test_logout_invalid_token(db_connection):
    """
    Tests that calling logout with an invalid token does not fail and returns False.
    """
    result = logout(db_connection, "invalid-token-string")
    assert result is False


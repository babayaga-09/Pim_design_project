# authorise_sqlite.py
import hashlib, secrets
from typing import Optional, NamedTuple
import sqlite3
from pim_types import AuthResult, Token
import bcrypt 

class User(NamedTuple):
    id: int
    username: str

# ------------------------------
# Helpers
# ------------------------------

def _hash_password(pw: str) -> str: # Return a string now
    pw_bytes = pw.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(pw_bytes, salt)
    return hashed_bytes.decode("utf-8") # Decode bytes to a clean string

def _verify_password(pw: str, pw_hash: str) -> bool: # Expect a string
    pw_bytes = pw.encode("utf-8")
    pw_hash_bytes = pw_hash.encode("utf-8") # Encode the string hash back to bytes
    return bcrypt.checkpw(pw_bytes, pw_hash_bytes)

def _new_token() -> str:
    return secrets.token_hex(16)


# ------------------------------
# Public API
# ------------------------------

def register_user(conn: sqlite3.Connection, username: str, password: str) -> bool:
    """Add a new user. Return False if already exists."""
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM users WHERE username = ?", (username,))
    if cur.fetchone():
        return False
    

    cur.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, _hash_password(password)))
    conn.commit()
    return True


def login(conn: sqlite3.Connection, username: str, password: str) -> AuthResult:
    """Check credentials and create session token if valid."""
    cur = conn.cursor()
    # The password_hash is now retrieved as bytes
    cur.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    if not row:
        return AuthResult(False, None, "User does not exist")
    
    # The password_hash from the DB is passed directly to verification
    if not _verify_password(password, row["password_hash"]):
        return AuthResult(False, None, "Invalid password")

    token = _new_token()
    cur.execute("INSERT INTO sessions (token, username) VALUES (?, ?)", (token, username))
    conn.commit()
    return AuthResult(True, token, "Login successful")


def logout(conn: sqlite3.Connection, session: Token) -> bool:
    """Remove session token if present."""
    cur = conn.cursor()
    cur.execute("DELETE FROM sessions WHERE token = ?", (session,))
    conn.commit()
    return cur.rowcount > 0


def whoami(conn: sqlite3.Connection, session: Token) -> Optional[User]:
    """Return user's ID and username if session is valid, else None."""
    cur = conn.cursor()
    cur.execute("""
        SELECT u.id, u.username
        FROM users u
        JOIN sessions s ON u.username = s.username
        WHERE s.token = ?
    """, (session,))
    row = cur.fetchone()
    return User(id=row["id"], username=row["username"]) if row else None

import uuid
from datetime import datetime  
from typing import Set
from pim_types import Particle, ParticleId
import sqlite3
import storage 
from authorise import User 

def new_uuid() -> str:
    """Generates a new unique identifier as a string."""
    return str(uuid.uuid4())

def now_iso() -> str:
    """Returns the current time in ISO 8601 format."""
    return datetime.now().isoformat()

def normalize_title(title: str) -> str:
    return " ".join(title.lower().split())


def create_particle(conn: sqlite3.Connection, user: User, title: str, body: str, tags: Set[str]) -> Particle:
    if not title.strip() or (not body.strip() and "<p><br></p>" not in body):
        raise ValueError("Title and body cannot be empty")

    cur = conn.cursor()
    cur.execute("SELECT 1 FROM particles WHERE lower(title) = ? AND author = ?", (title.lower(), user.username))
    if cur.fetchone():
        raise ValueError("You already have a particle with this title")

    # 1. Query for the highest current ID for this specific user.
    cur.execute("SELECT MAX(user_facing_id) FROM particles WHERE author = ?", (user.username,))
    
    # 2. Fetch the result. Might be None if the user has no particles yet.
    #    If it's None, we default to 0.
    max_id = cur.fetchone()[0] or 0
    
    # 3. The next ID is the highest existing ID plus one.
    next_id = max_id + 1


    p = Particle(
        id=new_uuid(),
        user_id=user.id,
        user_facing_id=next_id, 
        created_at=now_iso(),
        updated_at=now_iso(),
        title=title,
        body=body,
        tags=tags,
        author=user.username
    )
    storage.save_particle(conn, p)
    return p


def update_particle_title(conn: sqlite3.Connection, current_user: str, pid: ParticleId, new_title: str) -> Particle:
    if not new_title.strip():
        raise ValueError("Title cannot be empty")

    cur = conn.cursor()
    cur.execute("SELECT 1 FROM particles WHERE lower(title) = ? AND author = ? AND id != ?", (new_title.lower(), current_user, pid))
    if cur.fetchone():
        raise ValueError("You already have a particle with this title")

    particle = storage.get_particle(conn, pid)
    if not particle:
        raise KeyError("Particle not found")

    if particle.author != current_user:
        raise PermissionError("You do not have permission to modify this particle.")

    updated = particle._replace(
        title=new_title,
        updated_at=datetime.now().isoformat()
    )
    storage.save_particle(conn, updated)
    return updated


def update_particle_body(conn: sqlite3.Connection, current_user: str, pid: ParticleId, new_body: str) -> Particle:
    if not new_body.strip() and "<p><br></p>" not in new_body:
        raise ValueError("Body cannot be empty")

    particle = storage.get_particle(conn, pid)
    if not particle:
        raise KeyError("Particle not found")
        
    if particle.author != current_user:
        raise PermissionError("You do not have permission to modify this particle.")

    updated = particle._replace(
        body=new_body,
        updated_at=datetime.now().isoformat()
    )
    storage.save_particle(conn, updated)
    return updated


def add_tags(conn: sqlite3.Connection, current_user: str, pid: ParticleId, tags: Set[str]) -> Particle:
    particle = storage.get_particle(conn, pid)
    if not particle:
        raise KeyError("Particle not found")
        
    if particle.author != current_user:
        raise PermissionError("You do not have permission to modify this particle.")

    updated_tags = particle.tags.union(tags)
    updated = particle._replace(
        tags=updated_tags,
        updated_at=datetime.now().isoformat()
    )
    storage.save_particle(conn, updated)
    return updated


def remove_tags(conn: sqlite3.Connection, current_user: str, pid: ParticleId, tags: Set[str]) -> Particle:
    particle = storage.get_particle(conn, pid)
    if not particle:
        raise KeyError("Particle not found")
        
    if particle.author != current_user:
        raise PermissionError("You do not have permission to modify this particle.")

    updated_tags = particle.tags.difference(tags)
    updated = particle._replace(
        tags=updated_tags,
        updated_at=datetime.now().isoformat()
    )
    storage.save_particle(conn, updated)
    return updated


def delete_particle(conn: sqlite3.Connection, current_user: str, pid: ParticleId) -> bool:
    particle = storage.get_particle(conn, pid)
    if not particle:
        return True 

    if particle.author != current_user:
        raise PermissionError("You do not have permission to delete this particle.")

    return storage.delete_particle(conn, pid)

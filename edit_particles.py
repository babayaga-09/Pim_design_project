import uuid, datetime
from typing import Set
from pim_types import Particle, ParticleId
import sqlite3
import storage 


def normalize_title(title: str) -> str:
    return " ".join(title.lower().split())


def create_particle(conn: sqlite3.Connection, author: str, title: str, body: str, tags: Set[str]) -> Particle:
    if not title.strip() or not body.strip():
        raise ValueError("Title and body cannot be empty")

    cur = conn.cursor()
    cur.execute("SELECT 1 FROM particles WHERE lower(title) = ?", (title.lower(),))
    if cur.fetchone():
        raise ValueError("Title already exists")

    pid = str(uuid.uuid4())
    timestamp = datetime.datetime.now().isoformat()

    p = Particle(
        id=pid,
        title=title,
        body=body,
        author=author, 
        tags=set(tags),
        created_at=timestamp,
        updated_at=timestamp
    )
    storage.save_particle(conn, p)
    return p


def update_particle_title(conn: sqlite3.Connection, current_user: str, pid: ParticleId, new_title: str) -> Particle:
    if not new_title.strip():
        raise ValueError("Title cannot be empty")

    cur = conn.cursor()
    cur.execute("SELECT 1 FROM particles WHERE lower(title) = ?", (new_title.lower(),))
    if cur.fetchone():
        raise ValueError("Title already exists")

    particle = storage.get_particle(conn, pid)
    if not particle:
        raise KeyError("Particle not found")

    if particle.author != current_user:
        raise PermissionError("You do not have permission to modify this particle.")

    updated = particle._replace(
        title=new_title,
        updated_at=datetime.datetime.now().isoformat()
    )
    storage.save_particle(conn, updated)
    return updated


def update_particle_body(conn: sqlite3.Connection, current_user: str, pid: ParticleId, new_body: str) -> Particle:
    if not new_body.strip():
        raise ValueError("Body cannot be empty")

    particle = storage.get_particle(conn, pid)
    if not particle:
        raise KeyError("Particle not found")
        
    if particle.author != current_user:
        raise PermissionError("You do not have permission to modify this particle.")

    updated = particle._replace(
        body=new_body,
        updated_at=datetime.datetime.now().isoformat()
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
        updated_at=datetime.datetime.now().isoformat()
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
        updated_at=datetime.datetime.now().isoformat()
    )
    storage.save_particle(conn, updated)
    return updated


def delete_particle(conn: sqlite3.Connection, current_user: str, pid: ParticleId) -> bool:
    particle = storage.get_particle(conn, pid)
    if not particle:
        # If the particle doesn't exist, we can say it was deleted.
        return True 

    if particle.author != current_user:
        raise PermissionError("You do not have permission to delete this particle.")


    return storage.delete_particle(conn, pid)

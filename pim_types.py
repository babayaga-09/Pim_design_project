"""
pim_types defines the core data structures used throughout the PIM application, 
using NamedTuple allows for creating immutable, lightweight, and readable data objects.
"""

from typing import NamedTuple, Dict, Set, List, Optional


class Particle(NamedTuple):
    """represents a single piece of information ( a "particle")"""
    id: str
    user_id: int
    user_facing_id: int
    title: str
    body: str
    author: str
    tags: Set[str]
    created_at: str
    updated_at: str


class QueryHit(NamedTuple):
    """represents a single search result item"""
    id: str
    user_facing_id: int
    created_at: str #
    title: str
    score: float
    snippet: str


class Storage(NamedTuple):
    users: Dict[str, str]  # username -> password_hash
    sessions: Dict[str, str]  # token -> username
    particles: Dict[str, Particle]  # particle_id -> Particle
    titles: Dict[str, str]  # normalized title -> particle_id


class AuthResult(NamedTuple):
    ok: bool
    session: Optional[str]
    message: str


Token = str
ParticleId = str
 # type: ignore

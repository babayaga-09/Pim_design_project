from typing import NamedTuple, Dict, Set, List, Optional


class Particle(NamedTuple):
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

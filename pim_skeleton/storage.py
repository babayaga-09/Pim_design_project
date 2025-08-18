from typing import Dict, List, Optional
from models import Particle, ParticleCreate

_particles: Dict[int, Particle] = {}
_next_id = 1

def create_particle(p: ParticleCreate) -> Particle:
    global _next_id
    particle = Particle(id=_next_id, title=p.title, body=p.body)
    _particles[_next_id] = particle
    _next_id += 1
    return particle

def get_particle_by_id(particle_id: int) -> Optional[Particle]:
    return _particles.get(particle_id)

def search_particles(query: str) -> List[Particle]:
    q = query.strip().lower()
    if not q:
        # return recent (simple: id desc)
        return sorted(_particles.values(), key=lambda x: -x.id)
    return [
        p for p in _particles.values()
        if q in p.title.lower() or q in p.body.lower()
    ]

def update_particle(particle_id: int, p: ParticleCreate) -> bool:
    if particle_id in _particles:
        _particles[particle_id] = Particle(id=particle_id, title=p.title, body=p.body)
        return True
    return False

def delete_particle(particle_id: int) -> bool:
    return _particles.pop(particle_id, None) is not None

from typing import Dict, List, Optional
from api_models import Particle, ParticleCreate, ParticleUpdate

_particles: Dict[int, Particle] = {}    # _ indicating private variable
# keys :int_ ids,content: particle| also key = particle id
_next_id = 1

def create_particle(p: ParticleCreate) -> Particle:
    global _next_id
    particle = Particle(id=_next_id, title=p.title, body=p.body, tag = p.tag)
    _particles[_next_id] = particle
    _next_id += 1
    return particle      #creates a new particale with id

def get_particle_by_id(particle_id: int) -> Optional[Particle]:
    return _particles.get(particle_id)

def search_particles(query: str) -> Optional[List[Particle]]:
    q = query.strip().lower()
    title_results = [particles for particles in _particles.values()
               if q in particles.title.lower() or q in particles.body.lower()]
    tag_results = [particles for particles in _particles.values()
               if q in particles.tag.lower()]
    if title_results:   # for title or body found
        return title_results
    else:
        return None
#can create different search functions - by tag, title, date_added
    
#maybe can look at levenshtein distance later
#need to fix the update functio for chaning the parts of the particle accoringly
def update_particle(particle_id: int, p: ParticleUpdate) -> bool:
    if particle_id in _particles:
     existing = _particles[particle_id]
     updated_p = Particle(
     id = particle_id,
     title = existing.title if p.title is None else p.title,
     body =  existing.body if p.body is None else p.body,
     tag =   existing.tag if p.tag is None else p.tag     )
     _particles[particle_id] = updated_p
     return True
    #else
    else:
        return False
def delete_particle(particle_id: int) -> bool:
    return _particles.pop(particle_id, None) is not None

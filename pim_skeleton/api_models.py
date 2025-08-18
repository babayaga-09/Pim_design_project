#for request and response
from pydantic import BaseModel


class ParticleBase(BaseModel):
    title: str
    body: str

class ParticleCreate(ParticleBase):
    pass   #for input

class Particle(ParticleBase):
    id: int   #adding id to the particle
    class Config:
        from_attributes = True  # as pydantic expects only dict

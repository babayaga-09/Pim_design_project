#for request and response
#the type of data that comes and goes
from pydantic import BaseModel
from typing import Optional


class ParticleBase(BaseModel):  #shared schema , dont have to repeat now
    title: str                 #using basemodel , helps with conversion and validate
    body: str
    tag : list[str]

class ParticleCreate(ParticleBase): #inherit everything from particlebase
    pass   #for input
    
class ParticleUpdate(ParticleBase):
    title :Optional[str] = None
    body : Optional[str] = None
    tag : Optional[list[str]] = None
#for now updates only body and tags


class Particle(ParticleBase):
    id: int   #adding id to the particle
#    class Config:
 #       from_attributes = True  # as pydantic expects only dict
        
class UserCreate(BaseModel):  #taking inputs from the user
    username: str
    password: str

class User(UserCreate):    #giving an unique id to user
    id: int             #write function in bckend
    


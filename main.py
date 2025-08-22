from fastapi import FastAPI, HTTPException, Form
from typing import List
from fastapi.staticfiles import StaticFiles


#from models import Base
from db import init_db #for both user and particle
from api_models import User , Particle, ParticleCreate , UserCreate
from storage import auth_user



app = FastAPI(title="PIM (Particles) – SQLite version")
#create a db
@app.on_event("startup")
def on_startup():
    init_db()
    
    
#init_db

#just one front -end ; make changes later
app.mount("/", StaticFiles(directory="html_holder", html=True), name="html_holder")



@app.post("/signup", response_model=UserCreate)
def signup(user: UserCreate):
    success = storage.create_user(user)  # hashing happens inside storage
    if not success:
        raise HTTPException(status_code=400, detail="User already exists")
    return {"message": "User created successfully"}

@app.get("/login")
def login(user: User):
    if not storage.auth_user(user.username, user.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {"message": "Login successful"}


#Particle CRUD

#create [article
@app.post("/particles", response_model=Particle)
def create_particle(p: ParticleCreate):
    return storage.create_particle(p)
 
#for getting a particle  : Read
@app.get("/particles/{particle_id}", response_model=Particle)
def get_particle(particle_id: int):
    particle = storage.get_particle_by_id(particle_id)
    if not particle:
        raise HTTPException(status_code=404, detail="Not found")
    return particle

#this can be used for clicking on a specific particle
 
@app.get("/search/", response_model=List[Particle])
def search_particles(query: str):
    return storage.search_particles(query)
    
 #update particlew
@app.put("/particles/{particle_id}", response_model=Particle)
def update_particle(particle_id: int, particle: ParticleUpdate):
    updated = storage.update_particle(particle_id, particle)
    if not updated:
        raise HTTPException(status_code=404, detail="Particle not found")
    return Particle

#delete particle
@app.delete("/particles/{particle_id}")
def delete_particle(particle_id: int):
    if storage.delete_particle(particle_id):
        return {"message": "Deleted"}
    raise HTTPException(status_code=404, detail="Not found")



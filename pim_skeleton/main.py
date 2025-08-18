from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from db import SessionLocal, engine
from models import Base
from api_models import Particle, ParticleCreate
import crud
from auth import require_user

# Create DB tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="PIM (Particles) – SQLite version")

#just one front -end ; make changes later
app.mount("/", StaticFiles(directory="html_holder", html=True), name="html_holder")

#get DB session per request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#auth
@app.post("/login")
def login(user: str = Depends(require_user)):
    return {"message": "Login successful", "user": user}
    
    
@app.post("/login")
def login_route(username: str = Form(...), password: str = Form(...)):
    from auth import login, require_user
    if login(username, password):
        user = require_user()
        return {"message": "Login successful", "user": user}
    raise HTTPException(status_code=401, detail="Invalid credentials")

    
@app.get("/me")
def me():
    from auth import require_user
    user = require_user()
    return {"user": user}

# --- Particle CRUD ---

@app.post("/particles", response_model=Particle)
def create_particle(p: ParticleCreate, db: Session = Depends(get_db)):
    from auth import require_user
    user = require_user()
    return crud.create_particle(db, p)
    

@app.get("/particles/{particle_id}", response_model=Particle)
def get_particle(
    particle_id: int,
    db: Session = Depends(get_db),
    user: str = Depends(require_user),
):
    particle = crud.get_particle(db, particle_id)
    if not particle:
        raise HTTPException(status_code=404, detail="Not found")
    return particle

@app.get("/search", response_model=list[Particle])
def search(
    query: str = "",
    db: Session = Depends(get_db),
    user: str = Depends(require_user),
):
    return crud.search_particles(db, query)

@app.put("/particles/{particle_id}", response_model=Particle)
def update_particle(
    particle_id: int,
    p: ParticleCreate,
    db: Session = Depends(get_db),
    user: str = Depends(require_user),
):
    particle = crud.update_particle(db, particle_id, p)
    if particle:
        return particle
    raise HTTPException(status_code=404, detail="Not found")

@app.delete("/particles/{particle_id}")
def delete_particle(
    particle_id: int,
    db: Session = Depends(get_db),
    user: str = Depends(require_user),
):
    if crud.delete_particle(db, particle_id):
        return {"message": "Deleted"}
    raise HTTPException(status_code=404, detail="Not found")

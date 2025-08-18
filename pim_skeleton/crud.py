#like manager between the back and front end ; helping with retrieving particles from the database
from sqlalchemy.orm import Session
from models import ParticleORM
from api_models import ParticleCreate

# Create
def create_particle(db: Session, p: ParticleCreate) -> ParticleORM:
    db_particle = ParticleORM(title=p.title, body=p.body)
    db.add(db_particle)
    db.commit()
    db.refresh(db_particle)  # reload from DB with ID
    return db_particle

# Read one
def get_particle(db: Session, particle_id: int):
    return db.query(ParticleORM).filter(ParticleORM.id == particle_id).first()

# Read all / Search
def search_particles(db: Session, query: str = ""):
    return db.query(ParticleORM).filter(ParticleORM.title.contains(query)).all()

# Update
def update_particle(db: Session, particle_id: int, p: ParticleCreate):
    particle = db.query(ParticleORM).filter(ParticleORM.id == particle_id).first()
    if particle:
        particle.title = p.title
        particle.body = p.body
        db.commit()
        db.refresh(particle)
        return particle
    return None

# Delete
def delete_particle(db: Session, particle_id: int) -> bool:
    particle = db.query(ParticleORM).filter(ParticleORM.id == particle_id).first()
    if particle:
        db.delete(particle)
        db.commit()
        return True
    return False

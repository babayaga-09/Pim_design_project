
from sqlalchemy import Column, Integer, String, Text
from db import Base

class ParticleORM(Base):
    __tablename__ = "particles"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    body = Column(Text, nullable=False)



#class Particle(BaseModel):
 #   id: int
  #  title: str
   # body: str

#class ParticleCreate(BaseModel):
 #   title: str
  #  body: str



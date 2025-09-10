from fastapi import FastAPI, Depends, HTTPException # type: ignore
from pydantic import BaseModel # type: ignore
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import Optional, Set, List
import sqlite3


from storage import make_connection, get_particle
from authorise import register_user, login, logout, whoami
from edit_particles import create_particle, update_particle_body, update_particle_title, add_tags, remove_tags, delete_particle
from search import query
from pim_types import Particle, QueryHit, AuthResult


# FastAPI Setup

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
DB_PATH = "pim.db"


# Dependency: open connection for each request
def get_conn():
    conn = make_connection(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()


# Request/Response Models


class RegisterRequest(BaseModel):
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class ParticleRequest(BaseModel):
    title: str
    body: str
    tags: Set[str]

class UpdateBodyRequest(BaseModel):
    new_body: str

class UpdateTitleRequest(BaseModel):
    new_title: str

class TagUpdateRequest(BaseModel):
    tags: Set[str]

class SearchResponse(BaseModel):
    id: str
    user_facing_id: int
    created_at: str 
    title: str
    score: float
    snippet: str

class LogoutRequest(BaseModel):
    session: str

# New HTML Serving Endpoints

@app.get("/viewer.html", response_class=FileResponse)
async def read_viewer_page():
    return "templates/viewer.html"

@app.get("/editor.html", response_class=FileResponse)
async def read_editor_page():
    return "templates/editor.html"


# New Particle Data Endpoint

@app.get("/particles/{pid}")
def get_single_particle(pid: str, session: str, conn: sqlite3.Connection = Depends(get_conn)):
    user = whoami(conn, session)
    if not user:
        raise HTTPException(401, "Invalid session")
    
    particle = get_particle(conn, pid)
    if not particle:
        raise HTTPException(404, "Particle not found")
    
    if particle.author != user.username:
        raise HTTPException(403, "Permission denied")
    
    return particle._asdict()


# Auth Endpoints

@app.post("/register")
def register(req: RegisterRequest, conn: sqlite3.Connection = Depends(get_conn)):
    ok = register_user(conn, req.username, req.password)
    if not ok:
        raise HTTPException(400, "Username already exists")
    return {"message": "User registered"}


@app.post("/login")
def do_login(req: LoginRequest, conn: sqlite3.Connection = Depends(get_conn)):
    result: AuthResult = login(conn, req.username, req.password)
    if not result.ok:
        raise HTTPException(401, result.message)
    return {"session": result.session}


@app.post("/logout")
def do_logout(req: LogoutRequest, conn: sqlite3.Connection = Depends(get_conn)):
    ok = logout(conn, req.session)
    if not ok:
        raise HTTPException(400, "Invalid session")
    return {"message": "Logged out"}


@app.get("/whoami")
def do_whoami(session: str, conn: sqlite3.Connection = Depends(get_conn)):
    user = whoami(conn, session)
    if not user:
        raise HTTPException(401, "Invalid session")
    return {"username": user.username}

@app.get("/", response_class=FileResponse)
async def read_index():
    return "templates/login.html"

@app.get("/index.html", response_class=FileResponse)
async def read_main_page():
    return "templates/index.html"

# Particle Endpoints

@app.post("/particles")
def create(req: ParticleRequest, session: str, conn: sqlite3.Connection = Depends(get_conn)):
    user = whoami(conn, session)
    if not user:
        raise HTTPException(401, "Invalid session")
    p = create_particle(conn, user, req.title, req.body, req.tags)
    return p._asdict()


@app.put("/particles/{pid}/body")
def update_body(pid: str, req: UpdateBodyRequest, session: str, conn: sqlite3.Connection = Depends(get_conn)):
    user = whoami(conn, session)
    if not user:
        raise HTTPException(401, "Invalid session")
    updated = update_particle_body(conn, user.username, pid, req.new_body)
    return updated._asdict()


@app.put("/particles/{pid}/title")
def update_title(pid: str, req: UpdateTitleRequest, session: str, conn: sqlite3.Connection = Depends(get_conn)):
    user = whoami(conn, session)
    if not user:
        raise HTTPException(401, "Invalid session")
    updated = update_particle_title(conn, user.username, pid, req.new_title)
    return updated._asdict()


@app.put("/particles/{pid}/tags/add")
def add_particle_tags(pid: str, req: TagUpdateRequest, session: str, conn: sqlite3.Connection = Depends(get_conn)):
    user = whoami(conn, session)
    if not user:
        raise HTTPException(401, "Invalid session")
    updated = add_tags(conn, user.username, pid, req.tags)
    return updated._asdict()


@app.put("/particles/{pid}/tags/remove")
def remove_particle_tags(pid: str, req: TagUpdateRequest, session: str, conn: sqlite3.Connection = Depends(get_conn)):
    user = whoami(conn, session)
    if not user:
        raise HTTPException(401, "Invalid session")
    updated = remove_tags(conn, user.username, pid, req.tags)
    return updated._asdict()


@app.delete("/particles/{pid}")
def delete(pid: str, session: str, conn: sqlite3.Connection = Depends(get_conn)):
    user = whoami(conn, session)
    if not user:
        raise HTTPException(401, "Invalid session")
    ok = delete_particle(conn, user.username, pid)
    if not ok:
        raise HTTPException(404, "Particle not found")
    return {"message": "Particle deleted"}


# Search Endpoint

@app.get("/search", response_model=List[SearchResponse])
def search(q: str, session: str, conn: sqlite3.Connection = Depends(get_conn)):
    user = whoami(conn, session)
    if not user:
        raise HTTPException(401, "Invalid session")
    hits = query(conn, user.username, q)
    return [SearchResponse(**h._asdict()) for h in hits]

"""
This module defines the FastAPI web application, including all API endpoints
It handles routing, request/response models, dependency injection for database
connections, and orchestrates calls to other modules for business logic.
"""
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
    """ FastAPI dependency to create and manage a database connection per request
gives sqlite3.Connection: an active SQLite database connection """
    conn = make_connection(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()


# Request/Response Models


class RegisterRequest(BaseModel):
    """Request model for user registration"""
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class ParticleRequest(BaseModel):
    """Request model for creating a new particle"""
    title: str
    body: str
    tags: Set[str]

class UpdateBodyRequest(BaseModel):
     """Request model for updating a particles body"""
    new_body: str

class UpdateTitleRequest(BaseModel):
    """Model for updating a particles title"""

    new_title: str

class TagUpdateRequest(BaseModel):
    """Request model for adding or removing tags"""
    tags: Set[str]

class SearchResponse(BaseModel):
    """ response model for a single search result item"""
    id: str
    user_facing_id: int
    created_at: str 
    title: str
    score: float
    snippet: str

class LogoutRequest(BaseModel):
    session: str

# New HTML Serving Endpoints,
#handles GET requests from a users browser for specific HTML files like viewer and editor

@app.get("/viewer.html", response_class=FileResponse)
async def read_viewer_page():
    return "templates/viewer.html"

@app.get("/editor.html", response_class=FileResponse)
async def read_editor_page():
    return "templates/editor.html"


# New Particle Data Endpoint

@app.get("/particles/{pid}")
def get_single_particle(pid: str, session: str, conn: sqlite3.Connection = Depends(get_conn)):
    """
    Retrieves a single particle by its ID
    Args:
        pid: The unique identifier of the particle
        session: The user's session token for authentication
        conn: The database connection (dependency)
    Raises:
        HTTPException(401): If the session is invalid
        HTTPException(404): If the particle is not found
        HTTPException(403): If the user does not own the particle
    Returns:
        A dictionary representation of the Particle """
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
    """ Registers a new user
    Args:
        req: The registration request containing username and password
        conn: The database connection (dependency)
    Raises:
        HTTPException(400): If the username already exists
    Returns:
        A confirmation message """
    ok = register_user(conn, req.username, req.password)
    if not ok:
        raise HTTPException(400, "Username already exists")
    return {"message": "User registered"}


@app.post("/login")
def do_login(req: LoginRequest, conn: sqlite3.Connection = Depends(get_conn)):
    """ Logs a user in and provides a session token
    Args:
        req: The login request containing username and password
        conn: The database connection (dependency)
    Raises:
        HTTPException(401): If login fails
    Returns:
        A dictionary containing the session token """
    result: AuthResult = login(conn, req.username, req.password)
    if not result.ok:
        raise HTTPException(401, result.message)
    return {"session": result.session}


@app.post("/logout")
def do_logout(req: LogoutRequest, conn: sqlite3.Connection = Depends(get_conn)):
    """ Logs a user out by invalidating their session token
    Args:
        req: The logout request containing the session tokn
        conn: The database connection (dependency)
    Raises:
        HTTPException(400): If the session token is invalid
    Returns:
        A confirmation message """
    ok = logout(conn, req.session)
    if not ok:
        raise HTTPException(400, "Invalid session")
    return {"message": "Logged out"}


@app.get("/whoami")
def do_whoami(session: str, conn: sqlite3.Connection = Depends(get_conn)):
    """ identifies the user associated with a session token
    Args:
        session: The user's session token
        conn: The database connection (dependency)
    Raises:
        HTTPException(401): If the session is invalid
    Returns:
        A dictionary containing the username."""
    user = whoami(conn, session)
    if not user:
        raise HTTPException(401, "Invalid session")
    return {"username": user.username}

@app.get("/", response_class=FileResponse)
async def read_index():
    """Serves the main login page as the root URL"""
    return "templates/login.html"

@app.get("/index.html", response_class=FileResponse)
async def read_main_page():
    """Serves the main application landing page (dashboard)"""
    return "templates/index.html"

@app.get("/register.html", response_class=FileResponse)
async def read_register_page():
    ""Serves the user registration HTML page"""
    return "templates/register.html"

# Particle Endpoints

@app.post("/particles")
def create(req: ParticleRequest, session: str, conn: sqlite3.Connection = Depends(get_conn)):
    """ creates a new particle for the authenticated user
    Args:
        req:  request containing the particle's title, body, and tags.
        session:  user session token for authentication
        conn: database connection (dependency)
    Raises:
        HTTPException(401): If the session is invalid.
    Returns:
        A dictionary representation of the newly created Particle """
    user = whoami(conn, session)
    if not user:
        raise HTTPException(401, "Invalid session")
    p = create_particle(conn, user, req.title, req.body, req.tags)
    return p._asdict()


@app.put("/particles/{pid}/body")
def update_body(pid: str, req: UpdateBodyRequest, session: str, conn: sqlite3.Connection = Depends(get_conn)):
    """ updates the body of an existing particle
    Args:
        pid: The ID of the particle to update.
        req:  request containing the particle's title, body, and tags.
        session:  user session token for authentication
        conn: database connection (dependency)
    Raises:
        HTTPException(401): If the session is invalid
    Returns:
        A dictionary representation of the updated Particle """
    user = whoami(conn, session)
    if not user:
        raise HTTPException(401, "Invalid session")
    updated = update_particle_body(conn, user.username, pid, req.new_body)
    return updated._asdict()


@app.put("/particles/{pid}/title")
def update_title(pid: str, req: UpdateTitleRequest, session: str, conn: sqlite3.Connection = Depends(get_conn)):
""" Updates the title of an existing particle
    Args:
        pid: The ID of the particle to update
        req: The request containing the new title
        session: The user's session token for authentication
        conn: The database connection (dependency)
    Raises:
        HTTPException(401): If the session is invalid
    Returns:
        A dictionary representation of the updated Particle """
    user = whoami(conn, session)
    if not user:
        raise HTTPException(401, "Invalid session")
    updated = update_particle_title(conn, user.username, pid, req.new_title)
    return updated._asdict()


@app.put("/particles/{pid}/tags/add")
def add_particle_tags(pid: str, req: TagUpdateRequest, session: str, conn: sqlite3.Connection = Depends(get_conn)):
    """
    Adds one or more tags to a particle
    Args:
        pid: The ID of the particle to update
        req: The request containing the set of tags to add
        session: The user's session token for authentication
        conn: The database connection (dependency)
    Raises:
        HTTPException(401): If the session is invalid
    Returns:
        A dictionary representation of the updated Particle
    """
    user = whoami(conn, session)
    if not user:
        raise HTTPException(401, "Invalid session")
    updated = add_tags(conn, user.username, pid, req.tags)
    return updated._asdict()


@app.put("/particles/{pid}/tags/remove")
def remove_particle_tags(pid: str, req: TagUpdateRequest, session: str, conn: sqlite3.Connection = Depends(get_conn)):
    """
    Removes one or more tags from a particle
    Args:
        pid: The ID of the particle to update
        req: The request containing the set of tags to remove
        session: The user's session token for authentication
        conn: The database connection (dependency)
    Raises:
        HTTPException(401): If the session is invalid
    Returns:
        A dictionary representation of the updated Particle
    """

    user = whoami(conn, session)
    if not user:
        raise HTTPException(401, "Invalid session")
    updated = remove_tags(conn, user.username, pid, req.tags)
    return updated._asdict()


@app.delete("/particles/{pid}")
def delete(pid: str, session: str, conn: sqlite3.Connection = Depends(get_conn)):
    """
    deletes a particle
    Args:
        pid: The ID of the particle to delete
        session: The user's session token for authentication
        conn: The database connection (dependency)
    Raises:
        HTTPException(401): If the session is invalid
        HTTPException(404): If the particle is not found or already deleted
    Returns:
        A confirmation message
    """
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
    """
    Searches the user's particles by a query string
    Args:
        q: The search query string.
        session: The user's session token for authentication.
        conn: The database connection (dependency)
    Raises:
        HTTPException(401): If the session is invalid
    Returns:
        A list of search results
    """
    user = whoami(conn, session)
    if not user:
        raise HTTPException(401, "Invalid session")
    hits = query(conn, user.username, q)
    return [SearchResponse(**h._asdict()) for h in hits]

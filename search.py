from typing import List
import sqlite3
from pim_types import QueryHit, ParticleId


def query(conn: sqlite3.Connection, author: str, q: str, limit: int = 20) -> List[QueryHit]:
    """
    Search particles by title/body using LIKE queries for a specific author.
    Simple scoring: title match = 2, body match = 1.
    """
    q_like = f"%{q.lower()}%"
    cur = conn.cursor()

    cur.execute("""
        SELECT id, title, body,
            (CASE WHEN lower(title) LIKE ? THEN 2 ELSE 0 END) +
            (CASE WHEN lower(body) LIKE ? THEN 1 ELSE 0 END) AS score
        FROM particles
        WHERE author = ? AND (lower(title) LIKE ? OR lower(body) LIKE ?)
        ORDER BY score DESC
        LIMIT ?
    """, (q_like, q_like, author, q_like, q_like, limit)) 

    results: List[QueryHit] = []
    for row in cur.fetchall():
        snippet = row["body"][:60] + ("..." if len(row["body"]) > 60 else "")
        results.append(QueryHit(
            id=row["id"],
            title=row["title"],
            score=float(row["score"]),
            snippet=snippet
        ))
    return results

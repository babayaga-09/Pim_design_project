import sqlite3
import re
from typing import List, Dict, Any, Tuple
from pim_types import QueryHit

def parse_query(q: str) -> Tuple[List[str], List[str]]:
    """
    Parses a user's query into keywords and exact phrases.
    Phrases are identified by being enclosed in double quotes.
    Returns two lists: (keywords, phrases).
    """
    # This regex finds either quoted strings or non-space sequences
    tokens = re.findall(r'"[^"]+"|\S+', q)
    
    keywords = [word.lower() for word in tokens if not word.startswith('"')]
    phrases = [phrase.strip('"').lower() for phrase in tokens if phrase.startswith('"')]
    
    return keywords, phrases

def query(conn: sqlite3.Connection, author: str, q: str, limit: int = 20) -> List[QueryHit]:
    """
    Performs an optimized, multi-stage search without FTS5.
    - Handles multi-word AND logic, exact phrases, and improved scoring.
    - **FIXED**: Correctly returns all recent notes when the query string is empty.
    """
    cur = conn.cursor()

    # Handle the empty query case to show all notes 
    # If the search query is empty, fetch the most recent notes for the user.
    if not q.strip():
        cur.execute("""
            SELECT id, user_facing_id, title, body, created_at
            FROM particles
            WHERE author = ?
            ORDER BY user_facing_id DESC
            LIMIT ?
        """, (author, limit))
        
        all_notes = []
        for row in cur.fetchall():
            snippet = row["body"][:120] + ("..." if len(row["body"]) > 120 else "")
            all_notes.append(QueryHit(
                id=row["id"],
                user_facing_id=row["user_facing_id"],
                created_at=row["created_at"],
                title=row["title"],
                score=0, 
                snippet=snippet
            ))
        return all_notes

    # If the query is NOT empty, proceed 
    keywords, phrases = parse_query(q)
    all_terms = keywords + phrases
    
    if not all_terms:
        return []

    # Broad Candidate Selection (SQL) 
    where_conditions = []
    params = []
    for term in all_terms:
        like_term = f"%{term}%"
        where_conditions.append("(lower(title) LIKE ? OR lower(body) LIKE ?)")
        params.extend([like_term, like_term])
    
    sql_candidates = """
        SELECT id, user_facing_id, title, body, created_at
        FROM particles
        WHERE author = ? AND ({})
    """.format(" OR ".join(where_conditions))
    
    sql_params = tuple([author] + params)
    cur.execute(sql_candidates, sql_params)
    candidate_rows = cur.fetchall()

    # Precise Filtering & Scoring (Python) 
    final_results = []
    for row in candidate_rows:
        title_lower = row["title"].lower()
        body_lower = row["body"].lower()

        all_keywords_present = all(kw in title_lower or kw in body_lower for kw in keywords)
        all_phrases_present = all(ph in title_lower or ph in body_lower for ph in phrases)

        if not (all_keywords_present and all_phrases_present):
            continue

        score = 0
        for kw in keywords:
            if kw in title_lower: score += 5
            if kw in body_lower: score += 2
        for ph in phrases:
            if ph in title_lower: score += 20
            if ph in body_lower: score += 10

        final_results.append({"row": row, "score": score})

    sorted_results = sorted(final_results, key=lambda x: x["score"], reverse=True)
    
    output: List[QueryHit] = []
    for result in sorted_results[:limit]:
        row_data = result["row"]
        snippet = row_data["body"][:120] + ("..." if len(row_data["body"]) > 120 else "")
        output.append(QueryHit(
            id=row_data["id"],
            user_facing_id=row_data["user_facing_id"],
            created_at=row_data["created_at"],
            title=row_data["title"],
            score=result["score"],
            snippet=snippet
        ))

    return output


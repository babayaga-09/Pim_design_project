import sqlite3

def get_connection():
    conn = sqlite3.connect("particles.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row    #for getting dict instead of tuples
    return conn


#table if it doesnt exist
def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS particles(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        body TEXT NOT NULL,
        tag TEXT 
    )
    """)
    c.execute(""" CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)
    
    conn.commit()
    conn.close()

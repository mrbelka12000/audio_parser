import sqlite3

# Connect to database (creates file if it doesn't exist)

def connect():
    conn = sqlite3.connect("recordings.db")
    cur = conn.cursor()

# Create a table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS recordings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_path TEXT,
        transcript TEXT,
        analytics TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    return conn

def insert_transript(file_path, transcript):
    conn = connect()
    cur = conn.cursor()

    # Insert record
    cur.execute("""
        INSERT INTO recordings (file_path, transcript)
        VALUES (?, ?)
    """, (file_path, transcript))
    
    conn.commit()
    conn.close()


def update_analytics(file_path, analytics):
    conn = connect()
    cur = conn.cursor()

    # Update the analytics field for the matching file_path
    cur.execute("""
        UPDATE recordings
        SET analytics = ?
        WHERE file_path = ?
    """, (analytics, file_path))

    if cur.rowcount == 0:
        print(f"[DB] No record found for: {file_path}")
    else:
        print(f"[DB] Analytics updated for: {file_path}")
    
    conn.commit()
    conn.close()
    

def get_recording(file_path):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, file_path, transcript, analytics, created_at
        FROM recordings
        WHERE file_path = ?
    """, (file_path,))
    
    row = cur.fetchone()
    conn.close()

    if row:
        return {
            "id": row[0],
            "file_path": row[1],
            "transcript": row[2],
            "analytics": row[3],
            "created_at": row[4],
        }
    else:
        return None
    


def update_transcript(file_path, new_transcript):
    conn = connect()
    cur = conn.cursor()
    cur.execute("UPDATE recordings SET transcript = ? WHERE file_path = ?", (new_transcript, file_path))
    conn.commit()
    conn.close()

def update_analytics(file_path, new_analytics):
    conn = connect()
    cur = conn.cursor()
    cur.execute("UPDATE recordings SET analytics = ? WHERE file_path = ?", (new_analytics, file_path))
    conn.commit()
    conn.close()

def get_all_recordings():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, file_path, transcript, analytics, created_at
        FROM recordings
        ORDER BY created_at DESC
    """)
    
    rows = cur.fetchall()
    conn.close()

    recordings = []
    for row in rows:
        recordings.append({
            "id": row[0],
            "file_path": row[1],
            "transcript": row[2],
            "analytics": row[3],
            "created_at": row[4]
        })

    return recordings
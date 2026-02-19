import os
from psycopg2 import pool
from dotenv import load_dotenv
from .logger import get_logger

# Initialize logger for database
logger = get_logger("database")

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Use a connection pool for better performance
def create_pool():
    try:
        # Try DATABASE_URL first, but only if it looks complete
        if DATABASE_URL and "@" in DATABASE_URL:
            return pool.SimpleConnectionPool(1, 10, DATABASE_URL)
        
        # Fallback to individual parameters
        return pool.SimpleConnectionPool(
            1, 10,
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT")
        )
    except Exception as e:
        logger.error(f"Error creating connection pool: {e}")
        return None

db_pool = create_pool()

def get_connection():
    if db_pool:
        return db_pool.getconn()
    return None

def release_connection(conn):
    if db_pool and conn:
        db_pool.putconn(conn)

def check_db_health():
    """Check if the database is connected and responsive."""
    conn = get_connection()
    if not conn:
        return False
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False
    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
        release_connection(conn)

def migrate_schema(conn):
    """Handles migration from legacy integer user_id to firebase_uid TEXT."""
    cursor = conn.cursor()
    try:
        # Check bookmarks table
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='bookmarks' AND column_name='user_id'")
        has_user_id = cursor.fetchone()
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='bookmarks' AND column_name='firebase_uid'")
        has_firebase_uid = cursor.fetchone()

        if has_user_id and not has_firebase_uid:
            logger.info("Migrating 'bookmarks' table: user_id -> firebase_uid")
            # 1) Create firebase_uid as nullable
            cursor.execute("ALTER TABLE bookmarks ADD COLUMN firebase_uid TEXT")
            # 2) Populate firebase_uid from existing user_id (as a placeholder/mapping)
            cursor.execute("UPDATE bookmarks SET firebase_uid = CAST(user_id AS TEXT)")
            # 3) Now that all rows are populated, set NOT NULL
            cursor.execute("ALTER TABLE bookmarks ALTER COLUMN firebase_uid SET NOT NULL")
            
            cursor.execute("ALTER TABLE bookmarks DROP CONSTRAINT IF EXISTS bookmarks_user_id_movie_id_key")
            cursor.execute("ALTER TABLE bookmarks ADD CONSTRAINT bookmarks_firebase_uid_movie_id_key UNIQUE(firebase_uid, movie_id)")
            cursor.execute("ALTER TABLE bookmarks DROP COLUMN user_id")

        # Check ratings table
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='ratings' AND column_name='user_id'")
        has_user_id = cursor.fetchone()
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='ratings' AND column_name='firebase_uid'")
        has_firebase_uid = cursor.fetchone()

        if has_user_id and not has_firebase_uid:
            logger.info("Migrating 'ratings' table: user_id -> firebase_uid")
            # 1) Create firebase_uid as nullable
            cursor.execute("ALTER TABLE ratings ADD COLUMN firebase_uid TEXT")
            # 2) Populate firebase_uid from existing user_id
            cursor.execute("UPDATE ratings SET firebase_uid = CAST(user_id AS TEXT)")
            # 3) Now that all rows are populated, set NOT NULL
            cursor.execute("ALTER TABLE ratings ALTER COLUMN firebase_uid SET NOT NULL")
            
            cursor.execute("ALTER TABLE ratings DROP CONSTRAINT IF EXISTS ratings_user_id_movie_id_key")
            cursor.execute("ALTER TABLE ratings ADD CONSTRAINT ratings_firebase_uid_movie_id_key UNIQUE(firebase_uid, movie_id)")
            cursor.execute("ALTER TABLE ratings DROP COLUMN user_id")

        conn.commit()
    except Exception:
        conn.rollback()
        logger.exception("Database migration failed")
        raise
    finally:
        cursor.close()

def init_db():
    conn = get_connection()
    if not conn:
        return
    try:
        # First, run migrations if necessary
        migrate_schema(conn)
        
        cursor = conn.cursor()
        
        # Bookmarks table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookmarks (
            id SERIAL PRIMARY KEY,
            firebase_uid TEXT NOT NULL,
            movie_id INTEGER NOT NULL,
            movie_title TEXT NOT NULL,
            status TEXT NOT NULL, -- 'to_watch', 'watched'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(firebase_uid, movie_id)
        )
        """)
        
        # Ratings table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ratings (
            id SERIAL PRIMARY KEY,
            firebase_uid TEXT NOT NULL,
            movie_id INTEGER NOT NULL,
            movie_title TEXT NOT NULL,
            rating FLOAT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(firebase_uid, movie_id)
        )
        """)
        
        conn.commit()
        cursor.close()
    except Exception:
        conn.rollback()
        logger.exception("Failed to initialize database")
    finally:
        release_connection(conn)

def add_bookmark(firebase_uid, movie_id, movie_title, status):
    conn = get_connection()
    if not conn: return False
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO bookmarks (firebase_uid, movie_id, movie_title, status)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT(firebase_uid, movie_id) DO UPDATE SET status=EXCLUDED.status
        """, (firebase_uid, movie_id, movie_title, status))
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        logger.exception(f"Error adding bookmark for user {firebase_uid}, movie {movie_id}")
        return False
    finally:
        if cursor:
            cursor.close()
        release_connection(conn)

def remove_bookmark(firebase_uid, movie_id):
    conn = get_connection()
    if not conn: return False
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM bookmarks WHERE firebase_uid = %s AND movie_id = %s", (firebase_uid, movie_id))
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        logger.exception(f"Error removing bookmark for user {firebase_uid}, movie {movie_id}")
        return False
    finally:
        if cursor:
            cursor.close()
        release_connection(conn)

def get_user_bookmarks(firebase_uid):
    conn = get_connection()
    if not conn: return []
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT movie_id, movie_title, status FROM bookmarks WHERE firebase_uid = %s", (firebase_uid,))
        rows = cursor.fetchall()
        bookmarks = [{'movie_id': r[0], 'movie_title': r[1], 'status': r[2]} for r in rows]
        return bookmarks
    except Exception:
        logger.exception(f"Error fetching bookmarks for user {firebase_uid}")
        return []
    finally:
        if cursor:
            cursor.close()
        release_connection(conn)

def get_bookmark(firebase_uid, movie_id):
    conn = get_connection()
    if not conn: return None
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM bookmarks WHERE firebase_uid = %s AND movie_id = %s", (firebase_uid, movie_id))
        row = cursor.fetchone()
        return row[0] if row else None
    except Exception:
        logger.exception(f"Error fetching bookmark for user {firebase_uid}, movie {movie_id}")
        return None
    finally:
        if cursor:
            cursor.close()
        release_connection(conn)

def add_rating(firebase_uid, movie_id, movie_title, rating):
    conn = get_connection()
    if not conn: return False
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO ratings (firebase_uid, movie_id, movie_title, rating)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT(firebase_uid, movie_id) DO UPDATE SET rating=EXCLUDED.rating
        """, (firebase_uid, movie_id, movie_title, rating))
        conn.commit()
        return True
    except Exception:
        logger.exception(f"Error adding rating for user {firebase_uid}, movie {movie_id}")
        return False
    finally:
        if cursor:
            cursor.close()
        release_connection(conn)

def get_user_ratings(firebase_uid):
    conn = get_connection()
    if not conn: return []
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT movie_id, movie_title, rating FROM ratings WHERE firebase_uid = %s", (firebase_uid,))
        rows = cursor.fetchall()
        ratings = [{'movie_id': r[0], 'movie_title': r[1], 'rating': r[2]} for r in rows]
        return ratings
    except Exception:
        logger.exception(f"Error fetching ratings for user {firebase_uid}")
        return []
    finally:
        if cursor:
            cursor.close()
        release_connection(conn)

def get_rating(firebase_uid, movie_id):
    conn = get_connection()
    if not conn: return None
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT rating FROM ratings WHERE firebase_uid = %s AND movie_id = %s", (firebase_uid, movie_id))
        row = cursor.fetchone()
        return row[0] if row else None
    except Exception:
        logger.exception(f"Error fetching rating for user {firebase_uid}, movie {movie_id}")
        return None
    finally:
        if cursor:
            cursor.close()
        release_connection(conn)

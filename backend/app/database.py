from psycopg2 import pool

from .config import get_settings
from .logger import get_logger

# Initialize logger for database
logger = get_logger("database")

settings = get_settings()

DATABASE_URL = settings.DATABASE_URL

# Use a threaded connection pool for better performance and safety in multi-threaded environments
def create_pool():
    try:
        # Minimum 1, Maximum 10 connections
        # ThreadedConnectionPool is safer for uvicorn even in async environments
        if DATABASE_URL and "@" in DATABASE_URL:
            return pool.ThreadedConnectionPool(1, 10, DATABASE_URL)

        # Fallback to individual parameters
        return pool.ThreadedConnectionPool(
            1, 10,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            host=settings.DB_HOST,
            port=settings.DB_PORT
        )
    except Exception as e:
        logger.error(f"Error creating connection pool: {e}")
        raise RuntimeError(f"Failed to create database connection pool: {e}") from e

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
            cursor.execute("ALTER TABLE bookmarks ADD COLUMN firebase_uid TEXT")
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='users' AND column_name='firebase_uid'")
            if not cursor.fetchone():
                logger.error("Migration aborted: 'users.firebase_uid' column missing. Cannot map legacy users.")
                raise RuntimeError("users.firebase_uid column missing")

            cursor.execute("""
                UPDATE bookmarks b
                SET firebase_uid = u.firebase_uid
                FROM users u
                WHERE b.user_id = u.id
            """)

            cursor.execute("SELECT COUNT(*) FROM bookmarks WHERE firebase_uid IS NOT NULL")
            populated = cursor.fetchone()[0]
            if populated == 0:
                cursor.execute("SELECT COUNT(*) FROM bookmarks")
                total = cursor.fetchone()[0]
                if total > 0:
                    logger.error("Migration aborted: Bookmarks exist but none were mapped to a Firebase UID. Joining with 'users' failed.")
                    raise RuntimeError("Bookmark migration backfill failed: no matches found")

            cursor.execute("SELECT COUNT(*) FROM bookmarks WHERE firebase_uid IS NULL")
            orphans = cursor.fetchone()[0]
            if orphans > 0:
                logger.warning(f"Found {orphans} orphaned bookmarks. Removing data with no user mapping.")
                cursor.execute("DELETE FROM bookmarks WHERE firebase_uid IS NULL")

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
            cursor.execute("ALTER TABLE ratings ADD COLUMN firebase_uid TEXT")
            cursor.execute("""
                UPDATE ratings r
                SET firebase_uid = u.firebase_uid
                FROM users u
                WHERE r.user_id = u.id
            """)

            cursor.execute("SELECT COUNT(*) FROM ratings WHERE firebase_uid IS NOT NULL")
            populated = cursor.fetchone()[0]
            if populated == 0:
                cursor.execute("SELECT COUNT(*) FROM ratings")
                total = cursor.fetchone()[0]
                if total > 0:
                    logger.error("Migration aborted: Ratings exist but none were mapped to a Firebase UID. Joining with 'users' failed.")
                    raise RuntimeError("Rating migration backfill failed: no matches found")

            cursor.execute("SELECT COUNT(*) FROM ratings WHERE firebase_uid IS NULL")
            orphans = cursor.fetchone()[0]
            if orphans > 0:
                logger.warning(f"Found {orphans} orphaned ratings. Removing data with no user mapping.")
                cursor.execute("DELETE FROM ratings WHERE firebase_uid IS NULL")

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
        if cursor:
            cursor.close()

def init_db():
    conn = get_connection()
    if not conn:
        return
    try:
        migrate_schema(conn)
        with conn.cursor() as cursor:
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS bookmarks (
                id SERIAL PRIMARY KEY,
                firebase_uid TEXT NOT NULL,
                movie_id INTEGER NOT NULL,
                movie_title TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(firebase_uid, movie_id)
            )
            """)

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
    except Exception:
        conn.rollback()
        logger.exception("Failed to initialize database")
    finally:
        release_connection(conn)

import psycopg2
from psycopg2 import pool
import os
import hashlib
from dotenv import load_dotenv

load_dotenv()

from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

DATABASE_URL = os.getenv("DATABASE_URL")

def ensure_database_exists():
    dbname = os.getenv("DB_NAME", "moviedb")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")

    try:
        # Connect to the default 'postgres' database first
        conn = psycopg2.connect(
            dbname='postgres',
            user=user,
            password=password,
            host=host,
            port=port
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (dbname,))
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(f'CREATE DATABASE "{dbname}"')
            print(f"Database '{dbname}' created successfully!")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error ensuring database exists: {e}")

# Use a connection pool for better performance
def create_pool():
    # Ensure database exists specifically if we're using individual params
    # or if DATABASE_URL points to a local/managed instance we can control
    ensure_database_exists()
    
    try:
        # Try DATABASE_URL first, but only if it looks complete
        if DATABASE_URL and "@" in DATABASE_URL:
            return psycopg2.pool.SimpleConnectionPool(1, 10, DATABASE_URL)
        
        # Fallback to individual parameters
        return psycopg2.pool.SimpleConnectionPool(
            1, 10,
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT")
        )
    except Exception as e:
        print(f"Error creating connection pool: {e}")
        return None

db_pool = create_pool()

def get_connection():
    if db_pool:
        return db_pool.getconn()
    return None

def release_connection(conn):
    if db_pool and conn:
        db_pool.putconn(conn)

def init_db():
    conn = get_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
        """)
        
        # Bookmarks table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookmarks (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            movie_id INTEGER NOT NULL,
            movie_title TEXT NOT NULL,
            status TEXT NOT NULL, -- 'to_watch', 'watched'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, movie_id)
        )
        """)
        
        # Ratings table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ratings (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            movie_id INTEGER NOT NULL,
            movie_title TEXT NOT NULL,
            rating FLOAT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, movie_id)
        )
        """)
        
        conn.commit()
        cursor.close()
    finally:
        release_connection(conn)

def hash_password(password, username):
    salt = f"{username}_salt"
    return hashlib.sha256((password + salt).encode()).hexdigest()

def add_user(username, password):
    conn = get_connection()
    if not conn: return False
    try:
        cursor = conn.cursor()
        hashed_pw = hash_password(password, username)
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_pw))
        conn.commit()
        cursor.close()
        return True
    except Exception as e:
        print(f"Error adding user: {e}")
        return False
    finally:
        release_connection(conn)

def verify_user(username, password):
    conn = get_connection()
    if not conn: return None
    try:
        cursor = conn.cursor()
        hashed_pw = hash_password(password, username)
        cursor.execute("SELECT id FROM users WHERE username = %s AND password = %s", (username, hashed_pw))
        user = cursor.fetchone()
        cursor.close()
        return user[0] if user else None
    finally:
        release_connection(conn)

def get_user_id(username):
    conn = get_connection()
    if not conn: return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        return user[0] if user else None
    finally:
        release_connection(conn)

def add_bookmark(user_id, movie_id, movie_title, status):
    conn = get_connection()
    if not conn: return False
    try:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO bookmarks (user_id, movie_id, movie_title, status)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT(user_id, movie_id) DO UPDATE SET status=EXCLUDED.status
        """, (user_id, movie_id, movie_title, status))
        conn.commit()
        cursor.close()
        return True
    except Exception as e:
        print(f"Error adding bookmark: {e}")
        return False
    finally:
        release_connection(conn)

def remove_bookmark(user_id, movie_id):
    conn = get_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM bookmarks WHERE user_id = %s AND movie_id = %s", (user_id, movie_id))
        conn.commit()
        cursor.close()
    finally:
        release_connection(conn)

def get_user_bookmarks(user_id):
    conn = get_connection()
    if not conn: return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT movie_id, movie_title, status FROM bookmarks WHERE user_id = %s", (user_id,))
        rows = cursor.fetchall()
        bookmarks = [{'movie_id': r[0], 'movie_title': r[1], 'status': r[2]} for r in rows]
        cursor.close()
        return bookmarks
    finally:
        release_connection(conn)

def get_bookmark(user_id, movie_id):
    conn = get_connection()
    if not conn: return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM bookmarks WHERE user_id = %s AND movie_id = %s", (user_id, movie_id))
        row = cursor.fetchone()
        cursor.close()
        return row[0] if row else None
    finally:
        release_connection(conn)

def add_rating(user_id, movie_id, movie_title, rating):
    conn = get_connection()
    if not conn: return False
    try:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO ratings (user_id, movie_id, movie_title, rating)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT(user_id, movie_id) DO UPDATE SET rating=EXCLUDED.rating
        """, (user_id, movie_id, movie_title, rating))
        conn.commit()
        cursor.close()
        return True
    except Exception as e:
        print(f"Error adding rating: {e}")
        return False
    finally:
        release_connection(conn)

def get_user_ratings(user_id):
    conn = get_connection()
    if not conn: return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT movie_id, movie_title, rating FROM ratings WHERE user_id = %s", (user_id,))
        rows = cursor.fetchall()
        ratings = [{'movie_id': r[0], 'movie_title': r[1], 'rating': r[2]} for r in rows]
        cursor.close()
        return ratings
    finally:
        release_connection(conn)

def get_rating(user_id, movie_id):
    conn = get_connection()
    if not conn: return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT rating FROM ratings WHERE user_id = %s AND movie_id = %s", (user_id, movie_id))
        row = cursor.fetchone()
        cursor.close()
        return row[0] if row else None
    finally:
        release_connection(conn)

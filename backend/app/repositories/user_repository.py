from ..database import get_connection, release_connection, logger

class UserRepository:
    @staticmethod
    def add_bookmark(firebase_uid, movie_id, movie_title, status):
        conn = get_connection()
        if not conn:
            return False
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

    @staticmethod
    def remove_bookmark(firebase_uid, movie_id):
        conn = get_connection()
        if not conn:
            return False
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

    @staticmethod
    def get_user_bookmarks(firebase_uid):
        conn = get_connection()
        if not conn:
            return []
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

    @staticmethod
    def get_bookmark_status(firebase_uid, movie_id):
        conn = get_connection()
        if not conn:
            return None
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

    @staticmethod
    def add_rating(firebase_uid, movie_id, movie_title, rating):
        conn = get_connection()
        if not conn:
            return False
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
            if conn:
                conn.rollback()
            logger.exception(f"Error adding rating for user {firebase_uid}, movie {movie_id}")
            return False
        finally:
            if cursor:
                cursor.close()
            release_connection(conn)

    @staticmethod
    def get_user_ratings(firebase_uid):
        conn = get_connection()
        if not conn:
            return []
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

    @staticmethod
    def get_rating(firebase_uid, movie_id):
        conn = get_connection()
        if not conn:
            return None
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

    @staticmethod
    def delete_user_bookmarks(firebase_uid):
        """Delete all bookmarks for a user."""
        conn = get_connection()
        if not conn:
            return False
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM bookmarks WHERE firebase_uid = %s", (firebase_uid,))
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            logger.exception(f"Error deleting bookmarks for user {firebase_uid}")
            return False
        finally:
            if cursor:
                cursor.close()
            release_connection(conn)

    @staticmethod
    def delete_user_ratings(firebase_uid):
        """Delete all ratings for a user."""
        conn = get_connection()
        if not conn:
            return False
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM ratings WHERE firebase_uid = %s", (firebase_uid,))
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            logger.exception(f"Error deleting ratings for user {firebase_uid}")
            return False
        finally:
            if cursor:
                cursor.close()
            release_connection(conn)

    @staticmethod
    def delete_user_data_transactional(firebase_uid: str) -> bool:
        """Delete all user data (bookmarks and ratings) in a single transaction."""
        conn = get_connection()
        if not conn:
            return False
        cursor = None
        try:
            cursor = conn.cursor()
            # Delete bookmarks
            cursor.execute("DELETE FROM bookmarks WHERE firebase_uid = %s", (firebase_uid,))
            # Delete ratings
            cursor.execute("DELETE FROM ratings WHERE firebase_uid = %s", (firebase_uid,))
            # Delete preferences
            cursor.execute("DELETE FROM user_preferences WHERE firebase_uid = %s", (firebase_uid,))
            # Commit all deletes in a single transaction
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            logger.exception(f"Error deleting user data for user {firebase_uid}")
            return False
        finally:
            if cursor:
                cursor.close()
            release_connection(conn)

    @staticmethod
    def get_user_preferences(firebase_uid: str) -> dict:
        """Get user content preferences, returning defaults if not set."""
        conn = get_connection()
        if not conn:
            return {"filter_adult": False}
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT filter_adult FROM user_preferences WHERE firebase_uid = %s",
                (firebase_uid,)
            )
            row = cursor.fetchone()
            if row:
                return {"filter_adult": bool(row[0])}
            return {"filter_adult": False}
        except Exception:
            logger.exception(f"Error getting preferences for user {firebase_uid}")
            return {"filter_adult": False}
        finally:
            if cursor:
                cursor.close()
            release_connection(conn)

    @staticmethod
    def set_user_preferences(firebase_uid: str, filter_adult: bool) -> bool:
        """Upsert user content preferences."""
        conn = get_connection()
        if not conn:
            return False
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO user_preferences (firebase_uid, filter_adult, updated_at)
                VALUES (%s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (firebase_uid) DO UPDATE
                    SET filter_adult = EXCLUDED.filter_adult,
                        updated_at = CURRENT_TIMESTAMP
                """,
                (firebase_uid, filter_adult)
            )
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            logger.exception(f"Error setting preferences for user {firebase_uid}")
            return False
        finally:
            if cursor:
                cursor.close()
            release_connection(conn)

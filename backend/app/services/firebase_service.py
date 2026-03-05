import os
import firebase_admin
from firebase_admin import credentials
from ..logger import get_logger

logger = get_logger("firebase_service")

def init_firebase():
    """Initialize Firebase Admin SDK."""
    try:
        # Check if already initialized
        firebase_admin.get_app()
        logger.info("Firebase Admin already initialized.")
        return
    except ValueError:
        # Not initialized, so let's do it
        pass

    service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
    
    try:
        if service_account_path and os.path.exists(service_account_path):
            logger.info(f"Initializing Firebase with service account from: {service_account_path}")
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred)
        else:
            logger.info("Initializing Firebase with default credentials.")
            # This will try to use GOOGLE_APPLICATION_CREDENTIALS env var or metadata server
            try:
                firebase_admin.initialize_app()
            except Exception as e:
                logger.error(f"Failed to initialize Firebase with default credentials: {e}")
                # Fallback to dummy initialization if in local/test mode to prevent crashes
                # but log a major warning
                if os.getenv("ENVIRONMENT") != "production":
                    logger.warning("Using empty credentials for Firebase (test/local mode only).")
                    firebase_admin.initialize_app(credentials.AnonymousCredentials())
                else:
                    raise
        logger.info("Firebase Admin initialized successfully.")
    except Exception as e:
        logger.error(f"Critical error initializing Firebase: {e}")
        # In production we might want to let this fail to prevent unauthenticated access
        if os.getenv("ENVIRONMENT") == "production":
            raise

import os
import firebase_admin
from firebase_admin import credentials
from ..logger import get_logger

logger = get_logger("firebase_service")

def init_firebase():
    """Initialize Firebase Admin SDK."""
    # 1. If bypass for TESTING is set, skip initialization
    if os.getenv("TESTING") == "true":
        logger.info("TESTING mode: Skipping real Firebase initialization.")
        return

    try:
        # Check if already initialized
        firebase_admin.get_app()
        logger.info("Firebase Admin already initialized.")
        return
    except ValueError:
        pass

    # 2. Check for Firebase Emulator
    emulator_host = os.getenv("FIREBASE_EMULATOR_HOST")
    if emulator_host:
        logger.info(f"Using Firebase Emulator: {emulator_host}")
        # When using emulator, we can often initialize with default/dummy or explicit settings
        # but the FIREBASE_AUTH_EMULATOR_HOST env var managed by firebase-admin handles the routing
        if not firebase_admin._apps:
            firebase_admin.initialize_app()
        return

    service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
    
    try:
        if service_account_path and os.path.exists(service_account_path):
            logger.info(f"Initializing Firebase with service account from: {service_account_path}")
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred)
        else:
            logger.info("Initializing Firebase with default credentials.")
            try:
                firebase_admin.initialize_app()
            except Exception as e:
                logger.exception(f"Failed to initialize Firebase with default credentials: {str(e)}")
                # Removed AnonymousCredentials fallback as per requirement
                raise e
        logger.info("Firebase Admin initialized successfully.")
    except Exception as e:
        logger.exception(f"Critical error initializing Firebase: {str(e)}")
        # Always propagate the failure so callers (and tests) cannot continue with a failed initialization
        raise e

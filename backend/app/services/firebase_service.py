import os
import firebase_admin
from firebase_admin import credentials
from ..logger import get_logger

logger = get_logger("firebase_service")


def init_firebase() -> None:
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
        firebase_admin.initialize_app()
        return

    service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")

    # Fail fast if service account path is set but doesn't exist
    if service_account_path:
        if not os.path.exists(service_account_path):
            error_msg = f"FIREBASE_SERVICE_ACCOUNT_PATH is set to '{service_account_path}' but the file does not exist."
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        logger.info(f"Initializing Firebase with service account from: {service_account_path}")
        cred = credentials.Certificate(service_account_path)
        firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin initialized successfully.")
        return

    # Only attempt default credentials when env var is unset/empty
    logger.info("Initializing Firebase with default credentials.")
    try:
        firebase_admin.initialize_app()
    except Exception:
        logger.exception("Failed to initialize Firebase with default credentials")
        raise
    logger.info("Firebase Admin initialized successfully.")

import os
import firebase_admin
from firebase_admin import credentials

from ..logger import get_logger

logger = get_logger("firebase_service")


def init_firebase() -> None:
    """Initialize Firebase Admin SDK."""
    # 1. Skip initialization only when both TESTING and ALLOW_AUTH_BYPASS are "true"
    # This must match the auth-bypass gating in dependencies.py so auth paths
    # won't call Firebase when it hasn't been initialized.
    testing_value = os.getenv("TESTING", "").strip().lower()
    allow_bypass = os.getenv("ALLOW_AUTH_BYPASS", "").strip().lower()
    if testing_value == "true" and allow_bypass == "true":
        logger.info("TESTING + ALLOW_AUTH_BYPASS mode: Skipping Firebase initialization.")
        return

    try:
        # Check if already initialized
        firebase_admin.get_app()
        logger.info("Firebase Admin already initialized.")
        return
    except ValueError:
        pass

    # 2. Check for Firebase Emulator (service-specific env vars)
    emulator_vars = {
        "FIRESTORE_EMULATOR_HOST": os.getenv("FIRESTORE_EMULATOR_HOST"),
        "FIREBASE_AUTH_EMULATOR_HOST": os.getenv("FIREBASE_AUTH_EMULATOR_HOST"),
        "FIREBASE_DATABASE_EMULATOR_HOST": os.getenv("FIREBASE_DATABASE_EMULATOR_HOST"),
    }
    active_emulators = {k: v for k, v in emulator_vars.items() if v}
    if active_emulators:
        logger.info(f"Using Firebase Emulator(s): {active_emulators}")
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "demo-project")
        firebase_admin.initialize_app(
            credential=credentials.ApplicationDefault(),
            options={"projectId": project_id},
        )
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

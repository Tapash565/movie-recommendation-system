import os
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth

from ..config import get_settings
from ..logger import get_logger

logger = get_logger("firebase_service")


def init_firebase() -> None:
    """Initialize Firebase Admin SDK."""
    try:
        # Check if already initialized
        firebase_admin.get_app()
        logger.info("Firebase Admin already initialized.")
        return
    except ValueError:
        pass

    settings = get_settings()

    # Check for Firebase Emulator (legitimate for local development)
    emulator_vars = {
        "FIRESTORE_EMULATOR_HOST": os.getenv("FIRESTORE_EMULATOR_HOST"),
        "FIREBASE_AUTH_EMULATOR_HOST": os.getenv("FIREBASE_AUTH_EMULATOR_HOST"),
        "FIREBASE_DATABASE_EMULATOR_HOST": os.getenv("FIREBASE_DATABASE_EMULATOR_HOST"),
    }
    active_emulators = {k: v for k, v in emulator_vars.items() if v}
    if active_emulators:
        logger.info(f"Using Firebase Emulator(s): {active_emulators}")
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT") or settings.GOOGLE_CLOUD_PROJECT or "demo-project"
        firebase_admin.initialize_app(
            credential=credentials.ApplicationDefault(),
            options={"projectId": project_id},
        )
        return

    service_account_path = settings.FIREBASE_SERVICE_ACCOUNT_PATH

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

    # Use Google Cloud Project if set
    if settings.GOOGLE_CLOUD_PROJECT:
        logger.info(f"Initializing Firebase with Google Cloud Project: {settings.GOOGLE_CLOUD_PROJECT}")
        try:
            firebase_admin.initialize_app(
                credential=credentials.ApplicationDefault(),
                options={"projectId": settings.GOOGLE_CLOUD_PROJECT},
            )
        except Exception:
            logger.exception("Failed to initialize Firebase with Application Default Credentials")
            raise
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


def delete_firebase_user(uid: str) -> None:
    """Delete a Firebase user by UID."""
    try:
        firebase_auth.delete_user(uid)
        logger.info(f"Successfully deleted Firebase user: {uid}")
    except firebase_auth.UserNotFoundError:
        logger.warning(f"Firebase user not found: {uid}")
    except Exception:
        logger.exception(f"Failed to delete Firebase user: {uid}")
        raise

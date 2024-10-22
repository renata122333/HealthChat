import firebase_admin
from firebase_admin import credentials, db, storage
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get the credentials and configuration from environment variables
firebase_credentials_path = os.getenv('FIREBASE_CREDENTIALS_PATH')
firebase_database_url = os.getenv('FIREBASE_DATABASE_URL')
firebase_storage_bucket = os.getenv('FIREBASE_STORAGE_BUCKET')

# Flag to check if Firebase has already been initialized
firebase_initialized = False


def initialize_firebase():
    global firebase_initialized
    if not firebase_initialized:
        try:
            cred = credentials.Certificate(firebase_credentials_path)
            firebase_admin.initialize_app(cred, {
                'databaseURL': firebase_database_url,
                'storageBucket': firebase_storage_bucket
            })

            # Get references to Database and Storage
            db_ref = db.reference()
            bucket = storage.bucket()

            firebase_initialized = True
            print("Firebase successfully initialized.")
            return db_ref, bucket
        except Exception as e:
            print(f"Failed to initialize Firebase: {e}")
            return None, None
    else:
        print("Firebase already initialized.")
        return db.reference(), storage.bucket()


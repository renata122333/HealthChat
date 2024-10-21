import firebase_admin
from firebase_admin import credentials
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get the credentials and database URL from the environment variables
firebase_credentials_path = os.getenv('FIREBASE_CREDENTIALS_PATH')
firebase_database_url = os.getenv('FIREBASE_DATABASE_URL')

# Flag to check if Firebase has already been initialized
firebase_initialized = False

def initialize_firebase():
    if not firebase_admin._apps:
        try:
            cred = credentials.Certificate(firebase_credentials_path)
            firebase_admin.initialize_app(cred, {
                'databaseURL': firebase_database_url
            })
            print("Firebase successfully initialized.")
        except Exception as e:
            print(f"Failed to initialize Firebase: {e}")


import firebase_admin
from firebase_admin import credentials

def initialize_firebase():
    cred = credentials.Certificate('service_key.json')
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://heartchat-7268c-default-rtdb.firebaseio.com/'
    })

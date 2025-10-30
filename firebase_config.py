import firebase_admin
from firebase_admin import credentials, firestore

# 🔹 Replace this path with your actual Firebase service account key JSON path
FIREBASE_KEY = "unknown.json"

# Initialize Firebase only once
if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_KEY)
    firebase_admin.initialize_app(cred)

# Firestore client
db = firestore.client()

from flask import current_app, g 
from flask_pymongo import PyMongo

def get_db():
    """Configuration method to return a db instance

    """
    db = getattr(g, "_database", None)

    if db is None:
        db = g._database = PyMongo(current_app).db
        
    return db
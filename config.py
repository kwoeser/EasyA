import os

class Config:
    """Base configuration class."""
    SECRET_KEY = os.getenv("SECRET_KEY", "defaultsecretkey")
    # MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/easya")
    MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://kwoeser:Herbertpur@3@easya.brvnj.mongodb.net/?retryWrites=true&w=majority&appName=EasyA")
    

"""
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "defaultsecretkey")
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/easya")
"""

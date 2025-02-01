import os

class Config:
    """Base configuration class."""
    SECRET_KEY = os.getenv("SECRET_KEY", "defaultsecretkey")
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/easya")

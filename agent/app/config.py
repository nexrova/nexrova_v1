import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "super-secret-key-for-nexrova")
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_TYPE = 'filesystem'
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
    PMS_API_URL = os.environ.get("PMS_API_URL", "http://127.0.0.1:5000/api")
    HOTEL_INFO_PATH = os.path.join(os.path.dirname(__file__), '../hotel_info.txt')

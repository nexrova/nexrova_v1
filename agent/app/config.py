# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'super-secret-key-for-nexrova')
    SESSION_TYPE = 'filesystem'
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    PMS_API_URL = os.getenv('PMS_API_URL', 'http://127.0.0.1:5000/api')
    OLLAMA_API_URL = os.getenv('OLLAMA_API_URL', 'http://127.0.0.1:11434')
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'mistral')
    
    KEY_BOX_MAP = {
        '101': 'A1', '102': 'A2', '103': 'A3', '104': 'A4',
        '105': 'B1', '106': 'B2', '107': 'B3', '108': 'B4',
    }

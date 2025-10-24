import os
from dotenv import load_dotenv
load_dotenv()
class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    HOTEL_INFO = {
        'name': 'Chennai BnB Serviced Apartments',
        'location': 'Chennai, Tamil Nadu, India',
        'address': 'Thiru Nagar, Chennai',
        'total_rooms': 8,
        'contact': '+91-XXXXXXXXXX',
        'email': 'info@chennaibnb.com',
        'amenities': [
            'Free WiFi',
            '24/7 Reception',
            'Housekeeping',
            'Kitchen Facilities',
            'Parking'
        ],
        'check_in_time': '14:00',
        'check_out_time': '11:00'
    }

    @staticmethod
    def validate():
        if not Config.SUPABASE_URL or not Config.SUPABASE_KEY:
            print("⚠️  WARNING: SUPABASE_URL and SUPABASE_KEY not set!")
            print("   The app will run in demo mode with sample data.")
            print("   To connect to Supabase, set these environment variables.")
            return False
        return True

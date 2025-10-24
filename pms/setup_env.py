"""
Environment setup script for PMS
Run this to create your .env file with proper configuration
"""
import os

def create_env_file():
    env_content = """# Flask Configuration
SECRET_KEY=dev-secret-key-change-in-production
DEBUG=True
HOST=0.0.0.0
PORT=5000

# Supabase Configuration
SUPABASE_URL=your-supabase-url-here
SUPABASE_KEY=your-supabase-anon-key-here
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ Created .env file")
    print("📝 Please update SUPABASE_URL and SUPABASE_KEY with your actual Supabase credentials")

if __name__ == "__main__":
    create_env_file()

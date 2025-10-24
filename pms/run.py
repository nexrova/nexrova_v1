#!/usr/bin/env python3
"""
Simple startup script for the Hotel PMS
"""
import os
import sys
from pathlib import Path

def main():
    """Main startup function"""
    print("🏨 Hotel PMS Starting...")
    print("=" * 50)
    
    # Check if .env exists
    env_file = Path('.env')
    if not env_file.exists():
        print("⚠️  No .env file found!")
        print("   Run: python setup_env.py")
        print("   Then edit .env with your Supabase credentials")
        print()
    
    # Check if requirements are installed
    try:
        import flask
        import supabase
        print("✅ Dependencies found")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("   Run: pip install -r requirements.txt")
        return
    
    # Start the application
    try:
        from pms_app import create_app
        app = create_app()
        
        print("🚀 Starting Hotel PMS...")
        print("   Dashboard: http://localhost:5000")
        print("   API Docs: http://localhost:5000")
        print("   Press Ctrl+C to stop")
        print("=" * 50)
        
        app.run(host='0.0.0.0', port=5000, debug=True)
        
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        print("   Check your configuration and try again")

if __name__ == "__main__":
    main()

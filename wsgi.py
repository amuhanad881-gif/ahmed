#!/usr/bin/env python3
"""
WSGI entry point for Squad Talk
Use this file for production deployment
"""

print("=" * 60)
print("🔵 WSGI.PY STARTING")
print("=" * 60)

import os
import sys

# Print Python info
print(f"🐍 Python version: {sys.version}")
print(f"📂 Working directory: {os.getcwd()}")
print(f"📊 Environment variables available: {len(os.environ)}")

# Check critical env vars
print("\n🔍 Checking Environment Variables:")
print(f"   PORT: {os.environ.get('PORT', 'Not set ❌')}")
database_url = os.environ.get('DATABASE_URL')
print(f"   DATABASE_URL: {'Set ✅ (' + database_url[:30] + '...)' if database_url else 'Not set ❌'}")

print("\n📦 Importing app modules...")
try:
    from app import app, socketio, init_db, USE_DATABASE
    print("✅ App modules imported successfully")
    print(f"🗄️ USE_DATABASE status: {USE_DATABASE}")
except Exception as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("=" * 60)

if __name__ == "__main__":
    print("\n🔵 Initializing database...")
    
    # Initialize database
    try:
        init_db()
        print("✅ Database initialization completed")
    except Exception as e:
        print(f"⚠️ Database init warning: {e}")
        import traceback
        traceback.print_exc()
    
    # احصل على PORT من Railway
    port = int(os.environ.get("PORT", 5000))
    
    print(f"\n🚀 Starting SocketIO server...")
    print(f"   Host: 0.0.0.0")
    print(f"   Port: {port}")
    print(f"   Debug: False")
    print("=" * 60)
    
    # Production configuration
    socketio.run(
        app,
        host='0.0.0.0',
        port=port,
        debug=False,
        log_output=True
    )

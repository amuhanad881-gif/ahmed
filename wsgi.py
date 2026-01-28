#!/usr/bin/env python3
"""
WSGI entry point for Squad Talk
Use this file for production deployment
"""
from app import app, socketio
import os

if __name__ == "__main__":
    # احصل على PORT من Railway
    port = int(os.environ.get("PORT", 5000))
    
    print(f"🚀 Starting server on port {port}...")
    
    # Production configuration
    socketio.run(
        app,
        host='0.0.0.0',
        port=port,
        debug=False,
        log_output=True
    )

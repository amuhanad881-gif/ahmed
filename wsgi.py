#!/usr/bin/env python3
"""
WSGI entry point for EchoRoom
Production deployment file
"""

import eventlet
eventlet.monkey_patch()

from app import app, socketio
import os

if __name__ == "__main__":
    # Get port from Railway environment variable
    port = int(os.environ.get("PORT", 5000))
    
    # Production configuration
    socketio.run(
        app,
        host='0.0.0.0',
        port=port,
        debug=False
        # ⚠️ إزالة allow_unsafe_werkzeug ⚠️
    )

#!/usr/bin/env python3
"""
EchoRoom - Secure Voice & Text Chat with Gmail Validation
FULL VERSION - Railway.com & GitHub Hosting Ready
"""

import uuid
import hashlib
import json
import os
import smtplib
import ssl
import re
import secrets
import sqlite3
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template_string, request, g, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import eventlet

# Use eventlet for async
eventlet.monkey_patch()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'echo-room-secret-key-2025-railway')

# Initialize SocketIO with Redis for Railway
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='eventlet',
    manage_session=False,
    logger=True,
    engineio_logger=True
)

# Email Configuration (Railway Environment Variables)
EMAIL_SENDER = os.environ.get('EMAIL_SENDER', 'your-email@gmail.com')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', 'your-app-password')
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))

# Database Configuration for Railway
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///echoroom.db')
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

# Use SQLite for Railway (simpler)
def get_database_path():
    if 'RAILWAY_ENVIRONMENT' in os.environ:
        # On Railway, use persistent volume
        return '/data/echoroom.db'
    return 'echoroom.db'

DATABASE = get_database_path()

# Email validation regex
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@gmail\.com$'

# Session token expiry (30 days)
SESSION_EXPIRY_DAYS = 30

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# ==================== DATABASE FUNCTIONS ====================
def get_db():
    """Get database connection"""
    db = getattr(g, '_database', None)
    if db is None:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
        db = g._database = sqlite3.connect(DATABASE, check_same_thread=False)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    """Initialize database tables"""
    with app.app_context():
        db = get_db()
        
        # Users table
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                premium INTEGER DEFAULT 0,
                premium_until TEXT,
                created_at TEXT NOT NULL,
                verified INTEGER DEFAULT 0,
                last_login TEXT,
                avatar TEXT,
                banner TEXT,
                bio TEXT,
                status TEXT DEFAULT 'online'
            )
        ''')
        
        # Sessions table
        db.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                token TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                ip TEXT,
                FOREIGN KEY (email) REFERENCES users (email)
            )
        ''')
        
        # Rooms table
        db.execute('''
            CREATE TABLE IF NOT EXISTS rooms (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                type TEXT NOT NULL,
                creator TEXT NOT NULL,
                created_at TEXT NOT NULL,
                members TEXT,  -- JSON array of usernames
                invited TEXT   -- JSON array of usernames
            )
        ''')
        
        # Messages table
        db.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                display_name TEXT,
                message TEXT,
                server TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                type TEXT DEFAULT 'text',
                audio_data TEXT,
                duration INTEGER
            )
        ''')
        
        # Private messages table
        db.execute('''
            CREATE TABLE IF NOT EXISTS private_messages (
                id TEXT PRIMARY KEY,
                from_user TEXT NOT NULL,
                to_user TEXT NOT NULL,
                message TEXT,
                audio_data TEXT,
                duration INTEGER,
                timestamp TEXT NOT NULL,
                type TEXT DEFAULT 'text',
                read INTEGER DEFAULT 0
            )
        ''')
        
        # Friends table
        db.execute('''
            CREATE TABLE IF NOT EXISTS friends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user1 TEXT NOT NULL,
                user2 TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(user1, user2)
            )
        ''')
        
        # Friend requests table
        db.execute('''
            CREATE TABLE IF NOT EXISTS friend_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_user TEXT NOT NULL,
                to_user TEXT NOT NULL,
                created_at TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                UNIQUE(from_user, to_user)
            )
        ''')
        
        # Create indexes
        db.execute('CREATE INDEX IF NOT EXISTS idx_messages_server ON messages(server)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_private_messages_users ON private_messages(from_user, to_user)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_sessions_email ON sessions(email)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token)')
        
        db.commit()
        
        # Create default room if not exists
        default_room = db.execute('SELECT id FROM rooms WHERE id = "general"').fetchone()
        if not default_room:
            db.execute('''
                INSERT INTO rooms (id, name, description, type, creator, created_at, members, invited)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                'general',
                'General',
                'Welcome to EchoRoom!',
                'public',
                'system',
                datetime.now().isoformat(),
                json.dumps([]),
                json.dumps([])
            ))
            db.commit()
        
        print(f"✅ Database initialized at: {DATABASE}")

def close_connection(exception):
    """Close database connection"""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

app.teardown_appcontext(close_connection)

# ==================== HELPER FUNCTIONS ====================
def is_valid_gmail(email):
    """Check if email is a valid Gmail address"""
    return re.match(EMAIL_REGEX, email) is not None

def send_welcome_email(to_email, username):
    """Send welcome email to new users"""
    try:
        # Check if email credentials are set
        if not EMAIL_SENDER or not EMAIL_PASSWORD or EMAIL_SENDER == 'your-email@gmail.com':
            print("⚠️ Email not configured, skipping welcome email")
            return True
            
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Welcome to EchoRoom!"
        msg["From"] = EMAIL_SENDER
        msg["To"] = to_email
        
        # HTML Email Content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #00e5ff, #00b8d4); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                    <h1>🎤 EchoRoom</h1>
                    <p>Your new space for real-time communication</p>
                </div>
                <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
                    <p>Hi {username} 👋,</p>
                    
                    <p>Welcome to <strong>EchoRoom</strong> — your new space for real-time voice and chat communication.</p>
                    
                    <p>At EchoRoom, you can:</p>
                    <ul style="list-style: none; padding: 0;">
                        <li style="margin: 10px 0; padding-left: 25px; position: relative;">✅ 🎙️ Join voice rooms and talk instantly with friends</li>
                        <li style="margin: 10px 0; padding-left: 25px; position: relative;">✅ 💬 Chat in servers built around your interests</li>
                        <li style="margin: 10px 0; padding-left: 25px; position: relative;">✅ 🌍 Create your own rooms and connect with people anywhere</li>
                        <li style="margin: 10px 0; padding-left: 25px; position: relative;">✅ 🚀 Enjoy smooth, simple, and reliable communication</li>
                    </ul>
                    
                    <p>We're excited to have you with us and can't wait to see the communities you'll build.</p>
                    
                    <p>If you have any questions or feedback, we're always listening.</p>
                    
                    <p>See you inside EchoRoom,<br>
                    <strong>The EchoRoom Team</strong></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        text_content = f"""Hi {username} 👋,

Welcome to **EchoRoom** — your new space for real-time voice and chat communication.

We're excited to have you with us and can't wait to see the communities you'll build.

See you inside EchoRoom,
**The EchoRoom Team**"""
        
        # Attach both versions
        part1 = MIMEText(text_content, "plain")
        part2 = MIMEText(html_content, "html")
        msg.attach(part1)
        msg.attach(part2)
        
        # Create secure SSL context
        context = ssl.create_default_context()
        
        # Connect to SMTP server and send email
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls(context=context)
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, to_email, msg.as_string())
        
        print(f"📧 Welcome email sent to {to_email}")
        return True
    except Exception as e:
        print(f"⚠️ Failed to send email: {e}")
        return False

def generate_session_token():
    """Generate a secure session token"""
    return secrets.token_urlsafe(32)

def hash_password(password, salt=None):
    """Hash password with salt"""
    if salt is None:
        salt = secrets.token_hex(16)
    return hashlib.sha256((password + salt).encode()).hexdigest(), salt

def verify_password(password, hashed_password, salt):
    """Verify password against stored hash"""
    return hashlib.sha256((password + salt).encode()).hexdigest() == hashed_password

def create_session(email, ip='unknown'):
    """Create a new session for user"""
    db = get_db()
    token = generate_session_token()
    created_at = datetime.now().isoformat()
    expires_at = (datetime.now() + timedelta(days=SESSION_EXPIRY_DAYS)).isoformat()
    
    db.execute('''
        INSERT INTO sessions (email, token, created_at, expires_at, ip)
        VALUES (?, ?, ?, ?, ?)
    ''', (email, token, created_at, expires_at, ip))
    db.commit()
    
    return token

def validate_session(email, token):
    """Validate user session token"""
    db = get_db()
    
    # Get session
    session = db.execute('''
        SELECT * FROM sessions 
        WHERE email = ? AND token = ? AND expires_at > ?
    ''', (email, token, datetime.now().isoformat())).fetchone()
    
    if session:
        return True
    
    # Remove expired sessions
    db.execute('DELETE FROM sessions WHERE expires_at <= ?', (datetime.now().isoformat(),))
    db.commit()
    
    return False

def invalidate_all_sessions(email):
    """Invalidate all sessions for a user"""
    db = get_db()
    db.execute('DELETE FROM sessions WHERE email = ?', (email,))
    db.commit()
    return True

def are_friends(user1, user2):
    """Check if two users are friends"""
    db = get_db()
    friend = db.execute('''
        SELECT * FROM friends 
        WHERE (user1 = ? AND user2 = ?) OR (user1 = ? AND user2 = ?)
    ''', (user1, user2, user2, user1)).fetchone()
    
    return friend is not None

# ==================== DATABASE OPERATIONS ====================
def db_get_user(email):
    """Get user by email"""
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    return dict(user) if user else None

def db_get_user_by_username(username):
    """Get user by username"""
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    return dict(user) if user else None

def db_create_user(email, username, password_hash, salt):
    """Create new user"""
    db = get_db()
    created_at = datetime.now().isoformat()
    
    db.execute('''
        INSERT INTO users (email, username, password_hash, salt, created_at, avatar)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (email, username, password_hash, salt, created_at, f"https://ui-avatars.com/api/?name={username}&background=random&color=fff"))
    db.commit()

def db_update_user_last_login(email):
    """Update user last login time"""
    db = get_db()
    db.execute('UPDATE users SET last_login = ?, status = ? WHERE email = ?', 
              (datetime.now().isoformat(), 'online', email))
    db.commit()

def db_update_user_status(username, status):
    """Update user status"""
    db = get_db()
    db.execute('UPDATE users SET status = ? WHERE username = ?', (status, username))
    db.commit()

def db_activate_premium(email):
    """Activate premium for user"""
    db = get_db()
    premium_until = (datetime.now() + timedelta(days=30)).isoformat()
    db.execute('''
        UPDATE users 
        SET premium = 1, premium_until = ?
        WHERE email = ?
    ''', (premium_until, email))
    db.commit()

def db_update_user_profile(username, data):
    """Update user profile"""
    db = get_db()
    db.execute('''
        UPDATE users 
        SET avatar = ?, banner = ?, bio = ?
        WHERE username = ?
    ''', (data.get('avatar'), data.get('banner'), data.get('bio'), username))
    db.commit()

def db_get_rooms():
    """Get all rooms"""
    db = get_db()
    rooms = db.execute('SELECT * FROM rooms').fetchall()
    return [dict(room) for room in rooms]

def db_get_room(room_id):
    """Get room by ID"""
    db = get_db()
    room = db.execute('SELECT * FROM rooms WHERE id = ?', (room_id,)).fetchone()
    return dict(room) if room else None

def db_create_room(room_id, name, description, room_type, creator):
    """Create new room"""
    db = get_db()
    created_at = datetime.now().isoformat()
    
    db.execute('''
        INSERT INTO rooms (id, name, description, type, creator, created_at, members, invited)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        room_id,
        name,
        description,
        room_type,
        creator,
        created_at,
        json.dumps([creator]),
        json.dumps([])
    ))
    db.commit()

def db_delete_room(room_id):
    """Delete room"""
    db = get_db()
    db.execute('DELETE FROM rooms WHERE id = ?', (room_id,))
    db.execute('DELETE FROM messages WHERE server = ?', (room_id,))
    db.commit()

def db_get_room_members(room_id):
    """Get room members"""
    room = db_get_room(room_id)
    if not room:
        return []
    
    members = json.loads(room.get('members', '[]'))
    result = []
    for username in members:
        user = db_get_user_by_username(username)
        result.append({
            'username': username,
            'avatar': user.get('avatar') if user else None,
            'status': user.get('status', 'offline') if user else 'offline',
            'premium': bool(user.get('premium')) if user else False
        })
    return result

def db_add_user_to_room(room_id, username):
    """Add user to room"""
    db = get_db()
    room = db_get_room(room_id)
    if not room:
        return False
    
    members = json.loads(room.get('members', '[]'))
    if username not in members:
        members.append(username)
        
        db.execute('''
            UPDATE rooms 
            SET members = ?
            WHERE id = ?
        ''', (json.dumps(members), room_id))
        db.commit()
    
    return True

def db_remove_user_from_room(room_id, username):
    """Remove user from room"""
    db = get_db()
    room = db_get_room(room_id)
    if not room:
        return False
    
    members = json.loads(room.get('members', '[]'))
    if username in members:
        members.remove(username)
        
        db.execute('''
            UPDATE rooms 
            SET members = ?
            WHERE id = ?
        ''', (json.dumps(members), room_id))
        db.commit()
    
    return True

def db_save_message(message):
    """Save message to database"""
    db = get_db()
    
    db.execute('''
        INSERT OR REPLACE INTO messages (id, username, display_name, message, server, timestamp, type, audio_data, duration)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        message.get('id'),
        message.get('username'),
        message.get('display_name'),
        message.get('message'),
        message.get('server'),
        message.get('timestamp'),
        message.get('type', 'text'),
        message.get('audio_data'),
        message.get('duration')
    ))
    db.commit()

def db_save_private_message(message):
    """Save private message to database"""
    db = get_db()
    
    db.execute('''
        INSERT INTO private_messages (id, from_user, to_user, message, audio_data, duration, timestamp, type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        message.get('id'),
        message.get('from'),
        message.get('to'),
        message.get('message'),
        message.get('audio_data'),
        message.get('duration'),
        message.get('timestamp'),
        message.get('type', 'text')
    ))
    db.commit()

def db_get_messages(room_id, limit=100):
    """Get messages for a room"""
    db = get_db()
    messages = db.execute('''
        SELECT * FROM messages 
        WHERE server = ? 
        ORDER BY timestamp DESC 
        LIMIT ?
    ''', (room_id, limit)).fetchall()
    
    result = []
    for msg in messages:
        msg_dict = dict(msg)
        msg_dict['displayName'] = msg_dict.get('display_name')
        result.append(msg_dict)
    
    return result[::-1]  # Reverse to get chronological order

def db_get_private_messages(user1, user2, limit=100):
    """Get private messages between two users"""
    db = get_db()
    messages = db.execute('''
        SELECT * FROM private_messages 
        WHERE (from_user = ? AND to_user = ?) OR (from_user = ? AND to_user = ?)
        ORDER BY timestamp ASC 
        LIMIT ?
    ''', (user1, user2, user2, user1, limit)).fetchall()
    
    return [dict(msg) for msg in messages]

def db_add_friend_request(from_user, to_user):
    """Add friend request"""
    db = get_db()
    created_at = datetime.now().isoformat()
    
    try:
        db.execute('''
            INSERT INTO friend_requests (from_user, to_user, created_at)
            VALUES (?, ?, ?)
        ''', (from_user, to_user, created_at))
        db.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Request already exists

def db_get_friend_requests(username):
    """Get friend requests for user"""
    db = get_db()
    requests = db.execute('''
        SELECT from_user FROM friend_requests 
        WHERE to_user = ? AND status = 'pending'
    ''', (username,)).fetchall()
    
    return [row[0] for row in requests]

def db_accept_friend_request(from_user, to_user):
    """Accept friend request"""
    db = get_db()
    created_at = datetime.now().isoformat()
    
    # Update friend request status
    db.execute('''
        UPDATE friend_requests 
        SET status = 'accepted'
        WHERE from_user = ? AND to_user = ?
    ''', (from_user, to_user))
    
    # Add to friends table (both directions)
    db.execute('''
        INSERT OR IGNORE INTO friends (user1, user2, created_at)
        VALUES (?, ?, ?)
    ''', (from_user, to_user, created_at))
    
    db.execute('''
        INSERT OR IGNORE INTO friends (user1, user2, created_at)
        VALUES (?, ?, ?)
    ''', (to_user, from_user, created_at))
    
    db.commit()

def db_decline_friend_request(from_user, to_user):
    """Decline friend request"""
    db = get_db()
    db.execute('''
        DELETE FROM friend_requests 
        WHERE from_user = ? AND to_user = ?
    ''', (from_user, to_user))
    db.commit()

def db_get_friends(username):
    """Get user's friends"""
    db = get_db()
    friends = db.execute('''
        SELECT user2 as friend FROM friends WHERE user1 = ?
        UNION
        SELECT user1 as friend FROM friends WHERE user2 = ?
    ''', (username, username)).fetchall()
    
    return [row[0] for row in friends]

def db_remove_friend(user1, user2):
    """Remove friendship"""
    db = get_db()
    db.execute('''
        DELETE FROM friends 
        WHERE (user1 = ? AND user2 = ?) OR (user1 = ? AND user2 = ?)
    ''', (user1, user2, user2, user1))
    db.commit()

# ==================== ACTIVE USERS TRACKING ====================
active_users = {}  # username -> socket id
user_rooms = {}    # username -> current room id
socket_sessions = {}  # socket id -> session data

# ==================== HTML TEMPLATE ====================
HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎤 EchoRoom - Real-time Voice & Chat</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 100%);
            color: #fff; min-height: 100vh;
        }
        
        /* Loading Screen */
        .loading-screen {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 100%);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            z-index: 9999;
        }
        
        .loader {
            width: 50px;
            height: 50px;
            border: 3px solid rgba(0, 229, 255, 0.3);
            border-radius: 50%;
            border-top-color: #00e5ff;
            animation: spin 1s ease-in-out infinite;
            margin-bottom: 20px;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* Auth Modal */
        .auth-modal {
            display: flex;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.95);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }
        
        .auth-content {
            background: linear-gradient(135deg, rgba(30,30,40,0.95), rgba(20,20,30,0.95));
            padding: 40px;
            border-radius: 20px;
            width: 90%;
            max-width: 400px;
            border: 1px solid rgba(0,229,255,0.3);
            box-shadow: 0 0 50px rgba(0,229,255,0.2);
        }
        
        /* Main App */
        .app-container {
            display: none;
            height: 100vh;
            max-width: 1600px;
            margin: 0 auto;
        }
        
        .sidebar {
            width: 280px;
            background: rgba(20, 20, 30, 0.95);
            padding: 20px;
            overflow-y: auto;
            border-right: 1px solid rgba(255,255,255,0.1);
        }
        
        .main-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            background: rgba(25, 25, 35, 0.95);
        }
        
        /* Chat Styles */
        .chat-messages {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            background: rgba(15, 15, 25, 0.8);
        }
        
        .message {
            display: flex;
            gap: 15px;
            margin-bottom: 15px;
            animation: slideIn 0.3s ease;
        }
        
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .sidebar {
                width: 100%;
                height: auto;
                border-right: none;
                border-bottom: 1px solid rgba(255,255,255,0.1);
            }
            
            .app-container {
                flex-direction: column;
            }
        }
        
        /* Notifications */
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 25px;
            background: rgba(30,30,40,0.95);
            border-radius: 10px;
            border-left: 4px solid #00e5ff;
            animation: slideIn 0.3s ease;
            z-index: 2000;
        }
        
        .notification.success { border-left-color: #43b581; }
        .notification.error { border-left-color: #ff2e63; }
        .notification.info { border-left-color: #00e5ff; }
        
        /* Voice Recording */
        .voice-recording {
            position: fixed;
            bottom: 100px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(255, 46, 99, 0.95);
            color: white;
            padding: 15px 30px;
            border-radius: 25px;
            display: flex;
            align-items: center;
            gap: 10px;
            z-index: 1000;
            animation: pulse 1.5s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
    </style>
</head>
<body>
    <!-- Loading Screen -->
    <div class="loading-screen" id="loading-screen">
        <div class="loader"></div>
        <h2>🎤 EchoRoom</h2>
        <p>Loading amazing experience...</p>
    </div>
    
    <!-- Auth Modal -->
    <div class="auth-modal" id="auth-modal">
        <div class="auth-content">
            <h2 style="text-align: center; margin-bottom: 30px; color: #00e5ff;">
                <i class="fas fa-broadcast-tower"></i> EchoRoom
            </h2>
            
            <div style="margin-bottom: 20px;">
                <input type="email" id="login-email" placeholder="your@gmail.com" 
                       style="width: 100%; padding: 12px; margin-bottom: 10px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.2); background: rgba(255,255,255,0.1); color: white;">
                <input type="password" id="login-password" placeholder="Password" 
                       style="width: 100%; padding: 12px; margin-bottom: 15px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.2); background: rgba(255,255,255,0.1); color: white;">
                <button onclick="login()" style="width: 100%; padding: 12px; background: #00e5ff; border: none; border-radius: 8px; color: white; font-weight: bold; cursor: pointer;">
                    <i class="fas fa-sign-in-alt"></i> Login
                </button>
            </div>
            
            <div style="text-align: center; margin-top: 20px;">
                <p style="opacity: 0.7; margin-bottom: 10px;">Don't have an account?</p>
                <button onclick="showSignup()" style="padding: 10px 20px; background: transparent; border: 1px solid #00e5ff; border-radius: 8px; color: #00e5ff; cursor: pointer;">
                    Create Account
                </button>
            </div>
        </div>
    </div>
    
    <!-- Main App -->
    <div class="app-container" id="app-container">
        <!-- Sidebar -->
        <div class="sidebar">
            <div style="padding: 20px 0; border-bottom: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px;">
                <h2 style="color: #00e5ff; display: flex; align-items: center; gap: 10px;">
                    <i class="fas fa-broadcast-tower"></i> EchoRoom
                </h2>
                <p style="opacity: 0.7; font-size: 14px;">Real-time Voice & Chat</p>
            </div>
            
            <!-- User Profile -->
            <div id="user-profile" style="display: flex; align-items: center; gap: 15px; padding: 15px; background: rgba(0,0,0,0.2); border-radius: 10px; margin-bottom: 20px;">
                <div id="user-avatar" style="width: 50px; height: 50px; border-radius: 50%; background: rgba(0, 229, 255, 0.2); display: flex; align-items: center; justify-content: center; font-size: 20px;">
                    <i class="fas fa-user"></i>
                </div>
                <div style="flex: 1;">
                    <div id="username" style="font-weight: bold;"></div>
                    <div id="user-status" style="font-size: 12px; opacity: 0.7;">Online</div>
                </div>
            </div>
            
            <!-- Rooms List -->
            <div style="margin-bottom: 20px;">
                <h3 style="font-size: 14px; opacity: 0.7; margin-bottom: 10px;">ROOMS</h3>
                <div id="rooms-list"></div>
                <button onclick="createRoom()" style="width: 100%; padding: 10px; margin-top: 10px; background: rgba(0, 229, 255, 0.1); border: 1px dashed rgba(0, 229, 255, 0.3); border-radius: 8px; color: #00e5ff; cursor: pointer;">
                    <i class="fas fa-plus"></i> Create Room
                </button>
            </div>
            
            <!-- Friends List -->
            <div>
                <h3 style="font-size: 14px; opacity: 0.7; margin-bottom: 10px;">FRIENDS</h3>
                <div id="friends-list"></div>
                <button onclick="addFriend()" style="width: 100%; padding: 10px; margin-top: 10px; background: rgba(67, 181, 129, 0.1); border: 1px dashed rgba(67, 181, 129, 0.3); border-radius: 8px; color: #43b581; cursor: pointer;">
                    <i class="fas fa-user-plus"></i> Add Friend
                </button>
            </div>
        </div>
        
        <!-- Main Content -->
        <div class="main-content">
            <!-- Chat Header -->
            <div style="padding: 20px; background: rgba(0,0,0,0.3); border-bottom: 1px solid rgba(255,255,255,0.1); display: flex; justify-content: space-between; align-items: center;">
                <h2 id="current-room">
                    <i class="fas fa-hashtag"></i> General
                </h2>
                <div style="display: flex; gap: 10px;">
                    <div id="room-members-count" style="padding: 5px 10px; background: rgba(255,255,255,0.1); border-radius: 15px; font-size: 14px;">
                        <i class="fas fa-users"></i> <span id="members-count">0</span>
                    </div>
                    <button onclick="toggleVoice()" id="voice-btn" style="padding: 8px 15px; background: rgba(0, 229, 255, 0.2); border: 1px solid rgba(0, 229, 255, 0.3); border-radius: 8px; color: white; cursor: pointer;">
                        <i class="fas fa-microphone"></i> Voice
                    </button>
                </div>
            </div>
            
            <!-- Chat Messages -->
            <div class="chat-messages" id="chat-messages">
                <div style="text-align: center; padding: 40px 20px; opacity: 0.7;">
                    <i class="fas fa-comments" style="font-size: 48px; margin-bottom: 20px;"></i>
                    <h3>Welcome to EchoRoom!</h3>
                    <p>Start a conversation or join a voice chat</p>
                </div>
            </div>
            
            <!-- Message Input -->
            <div style="padding: 20px; background: rgba(0,0,0,0.3); border-top: 1px solid rgba(255,255,255,0.1); display: flex; gap: 10px;">
                <input type="text" id="message-input" placeholder="Type your message..." 
                       style="flex: 1; padding: 12px; border-radius: 25px; border: 1px solid rgba(255,255,255,0.2); background: rgba(255,255,255,0.1); color: white;">
                <button onclick="sendMessage()" style="width: 50px; height: 50px; border-radius: 50%; background: #00e5ff; border: none; color: white; cursor: pointer;">
                    <i class="fas fa-paper-plane"></i>
                </button>
                <button id="record-btn" onmousedown="startRecording()" onmouseup="stopRecording()" 
                        style="width: 50px; height: 50px; border-radius: 50%; background: rgba(255, 46, 99, 0.2); border: 1px solid rgba(255, 46, 99, 0.3); color: #ff2e63; cursor: pointer;">
                    <i class="fas fa-microphone"></i>
                </button>
            </div>
        </div>
    </div>
    
    <!-- Voice Recording Indicator -->
    <div class="voice-recording" id="voice-recording" style="display: none;">
        <div style="width: 12px; height: 12px; background: white; border-radius: 50%; animation: pulse 1s infinite;"></div>
        <span id="recording-timer">0:00</span>
        <span>Recording... Release to send</span>
    </div>
    
    <!-- Notification Container -->
    <div id="notification-container"></div>
    
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <script>
        let socket;
        let currentUser = '';
        let currentRoom = 'general';
        let isRecording = false;
        let recordingStartTime = null;
        let recordingTimer = null;
        
        // Initialize WebSocket
        function initSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const host = window.location.host;
            socket = io(`${protocol}//${host}`, {
                transports: ['websocket', 'polling'],
                reconnection: true,
                reconnectionAttempts: 5,
                reconnectionDelay: 1000
            });
            
            socket.on('connect', () => {
                console.log('✅ Connected to EchoRoom');
                showNotification('Connected to EchoRoom!', 'success');
                hideLoadingScreen();
                
                // Try auto-login
                const savedSession = localStorage.getItem('echoRoomSession');
                if (savedSession) {
                    try {
                        const session = JSON.parse(savedSession);
                        socket.emit('auto_login', {
                            email: session.email,
                            token: session.token
                        });
                        return;
                    } catch (e) {
                        console.log('No valid session found');
                    }
                }
                
                // Show auth modal if no session
                setTimeout(() => {
                    document.getElementById('auth-modal').style.display = 'flex';
                }, 500);
            });
            
            socket.on('connect_error', (error) => {
                console.log('❌ Connection error:', error);
                showNotification('Connection error. Retrying...', 'error');
            });
            
            // Login events
            socket.on('auto_login_success', (data) => {
                console.log('✅ Auto-login success');
                handleLoginSuccess(data);
            });
            
            socket.on('auto_login_error', () => {
                console.log('❌ Auto-login failed');
                document.getElementById('auth-modal').style.display = 'flex';
            });
            
            socket.on('login_success', (data) => {
                console.log('✅ Login success');
                handleLoginSuccess(data);
                
                // Save session
                localStorage.setItem('echoRoomSession', JSON.stringify({
                    email: data.email,
                    token: data.session_token,
                    username: data.username
                }));
            });
            
            socket.on('login_error', (data) => {
                showNotification(data.message || 'Login failed', 'error');
            });
            
            // Messages
            socket.on('message', (data) => {
                addMessage(data);
            });
            
            socket.on('private_message', (data) => {
                addMessage(data);
            });
            
            socket.on('chat_messages', (messages) => {
                const messagesDiv = document.getElementById('chat-messages');
                messagesDiv.innerHTML = '';
                if (messages && messages.length > 0) {
                    messages.forEach(msg => addMessage(msg));
                }
            });
            
            // Rooms
            socket.on('room_list', (rooms) => {
                updateRoomsList(rooms);
            });
            
            socket.on('room_joined', (data) => {
                currentRoom = data.room.id;
                document.getElementById('current-room').innerHTML = 
                    `<i class="fas fa-${data.room.type === 'voice' ? 'volume-up' : 'hashtag'}"></i> ${data.room.name}`;
                updateRoomMembers(data.members || []);
            });
            
            socket.on('room_members_updated', (members) => {
                updateRoomMembers(members);
            });
            
            // Friends
            socket.on('friends_list', (data) => {
                updateFriendsList(data.friends || []);
            });
            
            // Error handling
            socket.on('error', (data) => {
                showNotification(data.message || 'An error occurred', 'error');
            });
        }
        
        function hideLoadingScreen() {
            document.getElementById('loading-screen').style.opacity = '0';
            setTimeout(() => {
                document.getElementById('loading-screen').style.display = 'none';
            }, 300);
        }
        
        function showNotification(message, type = 'info') {
            const container = document.getElementById('notification-container');
            const notification = document.createElement('div');
            notification.className = `notification ${type}`;
            notification.textContent = message;
            container.appendChild(notification);
            
            setTimeout(() => notification.remove(), 3000);
        }
        
        function login() {
            const email = document.getElementById('login-email').value.trim();
            const password = document.getElementById('login-password').value.trim();
            
            if (!email || !password) {
                showNotification('Please fill all fields', 'error');
                return;
            }
            
            socket.emit('login', {
                email: email,
                password: password,
                remember_me: true
            });
        }
        
        function showSignup() {
            // Simple signup for demo
            const username = prompt('Enter username:');
            const email = prompt('Enter Gmail address:');
            const password = prompt('Enter password:');
            
            if (!username || !email || !password) {
                showNotification('All fields required', 'error');
                return;
            }
            
            socket.emit('signup', {
                username: username,
                email: email,
                password: password,
                remember_me: true
            });
        }
        
        function handleLoginSuccess(data) {
            currentUser = data.username;
            
            // Update UI
            document.getElementById('auth-modal').style.display = 'none';
            document.getElementById('app-container').style.display = 'flex';
            document.getElementById('username').textContent = currentUser;
            
            // Load data
            socket.emit('get_rooms');
            socket.emit('get_friends', { username: currentUser });
            socket.emit('join_room', { username: currentUser, room: 'general' });
            socket.emit('get_room_messages', { room: 'general' });
            
            showNotification(`Welcome ${currentUser}!`, 'success');
        }
        
        function sendMessage() {
            const input = document.getElementById('message-input');
            const message = input.value.trim();
            
            if (!message) return;
            
            socket.emit('message', {
                username: currentUser,
                message: message,
                server: currentRoom,
                timestamp: new Date().toISOString()
            });
            
            input.value = '';
            input.focus();
        }
        
        function addMessage(data) {
            const messagesDiv = document.getElementById('chat-messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message';
            
            const isOwn = data.username === currentUser;
            
            messageDiv.innerHTML = `
                <div style="width: 40px; height: 40px; border-radius: 50%; background: ${isOwn ? 'rgba(0, 229, 255, 0.3)' : 'rgba(67, 181, 129, 0.3)'}; display: flex; align-items: center; justify-content: center;">
                    ${data.username ? data.username.charAt(0).toUpperCase() : 'U'}
                </div>
                <div style="flex: 1;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <strong>${data.displayName || data.username || 'Unknown'}</strong>
                        <span style="opacity: 0.7; font-size: 12px;">
                            ${new Date(data.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                        </span>
                    </div>
                    <div>${data.message || 'Voice message'}</div>
                </div>
            `;
            
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        function updateRoomsList(rooms) {
            const list = document.getElementById('rooms-list');
            list.innerHTML = '';
            
            rooms.forEach(room => {
                const roomDiv = document.createElement('div');
                roomDiv.className = 'room-item';
                roomDiv.style.cssText = 'padding: 10px; margin: 5px 0; background: rgba(255,255,255,0.05); border-radius: 8px; cursor: pointer; transition: all 0.3s;';
                roomDiv.innerHTML = `
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <i class="fas fa-${room.type === 'voice' ? 'volume-up' : 'hashtag'}" style="color: ${room.type === 'voice' ? '#ff2e63' : '#00e5ff'}"></i>
                        <span>${room.name}</span>
                    </div>
                `;
                
                roomDiv.onclick = () => {
                    socket.emit('join_room', { 
                        username: currentUser,
                        room: room.id 
                    });
                    socket.emit('get_room_messages', { room: room.id });
                };
                
                list.appendChild(roomDiv);
            });
        }
        
        function updateFriendsList(friends) {
            const list = document.getElementById('friends-list');
            list.innerHTML = '';
            
            if (!friends || friends.length === 0) {
                list.innerHTML = '<div style="padding: 10px; opacity: 0.7; text-align: center;">No friends yet</div>';
                return;
            }
            
            friends.forEach(friend => {
                const friendDiv = document.createElement('div');
                friendDiv.style.cssText = 'padding: 10px; margin: 5px 0; background: rgba(255,255,255,0.05); border-radius: 8px; display: flex; align-items: center; gap: 10px;';
                friendDiv.innerHTML = `
                    <div style="width: 30px; height: 30px; border-radius: 50%; background: ${friend.connected ? 'rgba(67, 181, 129, 0.3)' : 'rgba(255,255,255,0.1)'}; display: flex; align-items: center; justify-content: center;">
                        <i class="fas fa-user" style="font-size: 12px;"></i>
                    </div>
                    <span>${friend.username}</span>
                    <span style="margin-left: auto; font-size: 10px; padding: 2px 8px; border-radius: 10px; background: ${friend.connected ? 'rgba(67, 181, 129, 0.2)' : 'rgba(255,255,255,0.1)'}; color: ${friend.connected ? '#43b581' : '#888'}">
                        ${friend.connected ? 'Online' : 'Offline'}
                    </span>
                `;
                
                friendDiv.onclick = () => {
                    startPrivateChat(friend.username);
                };
                
                list.appendChild(friendDiv);
            });
        }
        
        function updateRoomMembers(members) {
            document.getElementById('members-count').textContent = members.length;
        }
        
        function createRoom() {
            const name = prompt('Enter room name:');
            if (!name) return;
            
            const type = confirm('Voice room? (Cancel for text room)') ? 'voice' : 'text';
            
            socket.emit('create_room', {
                name: name,
                type: type,
                creator: currentUser
            });
        }
        
        function addFriend() {
            const username = prompt("Enter friend's username:");
            if (!username) return;
            
            socket.emit('send_friend_request', {
                from: currentUser,
                to: username
            });
        }
        
        function startPrivateChat(friend) {
            const sortedUsers = [currentUser, friend].sort();
            const roomId = `dm_${sortedUsers[0]}_${sortedUsers[1]}`;
            
            socket.emit('join_room', {
                username: currentUser,
                room: roomId
            });
            
            socket.emit('get_private_messages', {
                username: currentUser,
                friend: friend
            });
            
            document.getElementById('current-room').innerHTML = 
                `<i class="fas fa-user-friends"></i> ${friend}`;
        }
        
        function toggleVoice() {
            const btn = document.getElementById('voice-btn');
            const isVoice = btn.innerHTML.includes('Mute');
            
            btn.innerHTML = isVoice ? 
                '<i class="fas fa-microphone"></i> Voice' : 
                '<i class="fas fa-microphone-slash"></i> Mute';
            
            showNotification(isVoice ? 'Voice muted' : 'Voice enabled', 'info');
        }
        
        function startRecording() {
            if (!isRecording) {
                isRecording = true;
                recordingStartTime = Date.now();
                document.getElementById('voice-recording').style.display = 'flex';
                document.getElementById('record-btn').style.background = '#ff2e63';
                document.getElementById('record-btn').style.color = 'white';
                
                updateRecordingTimer();
                recordingTimer = setInterval(updateRecordingTimer, 1000);
            }
        }
        
        function stopRecording() {
            if (isRecording) {
                isRecording = false;
                clearInterval(recordingTimer);
                document.getElementById('voice-recording').style.display = 'none';
                document.getElementById('record-btn').style.background = 'rgba(255, 46, 99, 0.2)';
                document.getElementById('record-btn').style.color = '#ff2e63';
                
                // Send voice message placeholder
                const duration = Math.floor((Date.now() - recordingStartTime) / 1000);
                socket.emit('message', {
                    username: currentUser,
                    message: '🎤 Voice message (' + duration + 's)',
                    server: currentRoom,
                    timestamp: new Date().toISOString()
                });
            }
        }
        
        function updateRecordingTimer() {
            if (!recordingStartTime) return;
            
            const elapsed = Math.floor((Date.now() - recordingStartTime) / 1000);
            const minutes = Math.floor(elapsed / 60);
            const seconds = elapsed % 60;
            
            document.getElementById('recording-timer').textContent = 
                `${minutes}:${seconds.toString().padStart(2, '0')}`;
            
            if (elapsed >= 60) {
                stopRecording();
            }
        }
        
        // Initialize when page loads
        window.onload = function() {
            initSocket();
            
            // Enter key for message input
            document.getElementById('message-input').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') sendMessage();
            });
            
            // Enter key for login
            document.getElementById('login-password').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') login();
            });
        };
    </script>
</body>
</html>'''

# ==================== FLASK ROUTES ====================

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/health')
def health_check():
    """Health check endpoint for Railway"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'EchoRoom',
        'version': '2.0',
        'online_users': len(active_users)
    })

@app.route('/stats')
def get_stats():
    """Get application statistics"""
    try:
        db = get_db()
        
        stats = {
            'total_users': db.execute('SELECT COUNT(*) FROM users').fetchone()[0],
            'total_rooms': db.execute('SELECT COUNT(*) FROM rooms').fetchone()[0],
            'total_messages': db.execute('SELECT COUNT(*) FROM messages').fetchone()[0],
            'total_private_messages': db.execute('SELECT COUNT(*) FROM private_messages').fetchone()[0],
            'online_users': len(active_users),
            'premium_users': db.execute('SELECT COUNT(*) FROM users WHERE premium = 1').fetchone()[0]
        }
        
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ==================== SOCKETIO EVENTS ====================

@socketio.on('connect')
def handle_connect():
    print(f"✅ Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    # Update user status to offline
    for username, sid in list(active_users.items()):
        if sid == request.sid:
            del active_users[username]
            db_update_user_status(username, 'offline')
            
            # Remove from user rooms
            if username in user_rooms:
                room_id = user_rooms[username]
                del user_rooms[username]
                
                # Update room members
                if room_id in rooms_db:
                    socketio.emit('room_members_updated', 
                                db_get_room_members(room_id),
                                room=room_id)
            
            print(f"❌ User disconnected: {username}")
            break
    
    # Remove socket session
    if request.sid in socket_sessions:
        del socket_sessions[request.sid]
    
    print(f"📊 Active users: {len(active_users)}")

# Authentication events
@socketio.on('auto_login')
def handle_auto_login(data):
    email = data.get('email')
    token = data.get('token')
    
    if not email or not token:
        emit('auto_login_error', {'message': 'Invalid session'})
        return
    
    if not validate_session(email, token):
        emit('auto_login_error', {'message': 'Session expired'})
        return
    
    user = db_get_user(email)
    if not user:
        emit('auto_login_error', {'message': 'User not found'})
        return
    
    username = user['username']
    
    # Store session
    socket_sessions[request.sid] = {
        'email': email,
        'token': token,
        'username': username
    }
    
    active_users[username] = request.sid
    db_update_user_status(username, 'online')
    
    emit('auto_login_success', {
        'username': username,
        'email': email,
        'premium': bool(user['premium']),
        'session_token': token
    })

@socketio.on('signup')
def handle_signup(data):
    username = data.get('username', '').strip()
    email = data.get('email', '').lower().strip()
    password = data.get('password', '')
    remember_me = data.get('remember_me', True)
    
    # Validation
    if not username or not email or not password:
        emit('signup_error', {'message': 'All fields required'})
        return
    
    if not is_valid_gmail(email):
        emit('signup_error', {'message': 'Please use a valid Gmail address (@gmail.com)'})
        return
    
    # Check if email already exists
    if db_get_user(email):
        emit('signup_error', {'message': 'Email already registered'})
        return
    
    # Check if username already exists
    if db_get_user_by_username(username):
        emit('signup_error', {'message': 'Username already taken'})
        return
    
    # Hash password
    hashed_password, salt = hash_password(password)
    
    # Create user
    try:
        db_create_user(email, username, hashed_password, salt)
    except Exception as e:
        emit('signup_error', {'message': 'Database error: ' + str(e)})
        return
    
    # Create session if remember me is enabled
    session_token = None
    if remember_me:
        session_token = create_session(email, request.remote_addr)
    
    # Send welcome email
    send_welcome_email(email, username)
    
    emit('signup_success', {
        'message': 'Account created successfully',
        'email': email,
        'session_token': session_token
    })

@socketio.on('login')
def handle_login(data):
    email = data.get('email', '').lower().strip()
    password = data.get('password', '')
    remember_me = data.get('remember_me', True)
    
    user = db_get_user(email)
    if not user:
        emit('login_error', {'message': 'Invalid email or password'})
        return
    
    # Verify password
    if not verify_password(password, user['password_hash'], user['salt']):
        emit('login_error', {'message': 'Invalid email or password'})
        return
    
    username = user['username']
    
    # Create session
    session_token = None
    if remember_me:
        session_token = create_session(email, request.remote_addr)
    
    # Store session
    socket_sessions[request.sid] = {
        'email': email,
        'token': session_token,
        'username': username
    }
    
    active_users[username] = request.sid
    db_update_user_last_login(email)
    db_update_user_status(username, 'online')
    
    emit('login_success', {
        'username': username,
        'email': email,
        'premium': bool(user['premium']),
        'session_token': session_token
    })

# Chat events
@socketio.on('message')
def handle_message(data):
    if request.sid not in socket_sessions:
        emit('session_expired', {'message': 'Please login again'})
        return
    
    session = socket_sessions[request.sid]
    username = session['username']
    message_text = data.get('message', '').strip()
    server = data.get('server')
    
    if not message_text or not server:
        return
    
    message_id = str(uuid.uuid4())[:8]
    user = db_get_user_by_username(username)
    
    message = {
        'id': message_id,
        'username': username,
        'display_name': username,
        'message': message_text,
        'server': server,
        'timestamp': data.get('timestamp', datetime.now().isoformat()),
        'type': 'text'
    }
    
    db_save_message(message)
    
    # Prepare for sending
    message['displayName'] = message['display_name']
    
    print(f"📨 Message sent: {username} -> {server}")
    emit('message', message, room=server)

@socketio.on('private_message')
def handle_private_message(data):
    if request.sid not in socket_sessions:
        emit('session_expired', {'message': 'Please login again'})
        return
    
    session = socket_sessions[request.sid]
    from_user = session['username']
    to_user = data.get('to')
    message_text = data.get('message', '').strip()
    
    if not to_user or not message_text:
        emit('private_message_error', {'message': 'Missing required fields'})
        return
    
    # Check if users are friends
    if not are_friends(from_user, to_user):
        emit('private_message_error', {'message': 'You can only message friends'})
        return
    
    message_id = str(uuid.uuid4())[:8]
    
    message = {
        'id': message_id,
        'from': from_user,
        'to': to_user,
        'message': message_text,
        'timestamp': data.get('timestamp', datetime.now().isoformat()),
        'type': 'text'
    }
    
    db_save_private_message(message)
    
    # Create consistent room ID
    sorted_users = sorted([from_user, to_user])
    room_id = f"dm_{sorted_users[0]}_{sorted_users[1]}"
    
    # Prepare message for both users
    formatted_message = {
        'id': message_id,
        'username': from_user,
        'displayName': from_user,
        'message': message_text,
        'timestamp': message['timestamp'],
        'server': room_id,
        'type': 'private'
    }
    
    socketio.emit('private_message', formatted_message, room=room_id)
    print(f"📨 Private message: {from_user} -> {to_user}")

@socketio.on('get_private_messages')
def handle_get_private_messages(data):
    if request.sid not in socket_sessions:
        return
    
    session = socket_sessions[request.sid]
    username = session['username']
    friend = data.get('friend')
    
    if not friend:
        emit('private_messages_error', {'message': 'Friend username required'})
        return
    
    # Check if users are friends
    if not are_friends(username, friend):
        emit('private_messages_error', {'message': 'You can only view messages with friends'})
        return
    
    messages = db_get_private_messages(username, friend)
    
    # Create consistent room ID
    sorted_users = sorted([username, friend])
    room_id = f"dm_{sorted_users[0]}_{sorted_users[1]}"
    
    # Format messages for display
    formatted_messages = []
    for msg in messages:
        formatted_messages.append({
            'id': msg['id'],
            'username': msg['from_user'],
            'displayName': msg['from_user'],
            'message': msg['message'],
            'server': room_id,
            'timestamp': msg['timestamp'],
            'type': 'private'
        })
    
    emit('private_messages', {
        'friend': friend,
        'room_id': room_id,
        'messages': formatted_messages
    })

@socketio.on('get_room_messages')
def handle_get_room_messages(data):
    if request.sid not in socket_sessions:
        return
    
    room_id = data.get('room')
    
    if not room_id:
        return
    
    # Check if it's a private chat room
    if room_id.startswith('dm_'):
        # Extract usernames from room ID
        parts = room_id.split('_')
        if len(parts) == 3:
            user1, user2 = parts[1], parts[2]
            session = socket_sessions[request.sid]
            username = session['username']
            
            # Determine which friend this chat is with
            friend = user2 if user1 == username else user1
            
            # Get private messages
            handle_get_private_messages({
                'friend': friend
            })
    else:
        # Regular room messages
        room_messages = db_get_messages(room_id, limit=100)
        emit('chat_messages', room_messages)

# Room events
@socketio.on('join_room')
def handle_join_room(data):
    if request.sid not in socket_sessions:
        emit('session_expired', {'message': 'Please login again'})
        return
    
    session = socket_sessions[request.sid]
    username = session['username']
    room_id = data.get('room')
    
    if not room_id:
        emit('room_join_error', {'message': 'Room ID required'})
        return
    
    # Check if it's a private chat room
    if room_id.startswith('dm_'):
        # Extract usernames from room ID
        parts = room_id.split('_')
        if len(parts) == 3:
            user1, user2 = parts[1], parts[2]
            
            # Check if user is part of this DM
            if username not in [user1, user2]:
                emit('room_join_error', {'message': 'Not authorized to join this private chat'})
                return
            
            join_room(room_id)
            user_rooms[username] = room_id
            
            print(f"✅ {username} joined private chat: {room_id}")
            
            emit('room_joined', {
                'room': {'id': room_id, 'type': 'dm', 'name': user2 if user1 == username else user1},
                'members': []
            })
        return
    
    # Regular room joining logic
    room = db_get_room(room_id)
    if not room:
        emit('room_join_error', {'message': 'Room not found'})
        return
    
    join_room(room_id)
    user_rooms[username] = room_id
    
    # Add user to room members if not already
    db_add_user_to_room(room_id, username)
    
    print(f"✅ {username} joined room: {room_id}")
    
    emit('room_joined', {
        'room': room,
        'members': db_get_room_members(room_id)
    })
    
    socketio.emit('room_members_updated', 
                 db_get_room_members(room_id),
                 room=room_id)

@socketio.on('get_rooms')
def handle_get_rooms():
    if request.sid not in socket_sessions:
        return
    
    rooms = db_get_rooms()
    emit('room_list', rooms)

@socketio.on('create_room')
def handle_create_room(data):
    if request.sid not in socket_sessions:
        emit('session_expired', {'message': 'Please login again'})
        return
    
    session = socket_sessions[request.sid]
    username = session['username']
    room_name = data.get('name', '').strip()
    room_type = data.get('type', 'text')
    
    if not room_name:
        emit('room_created_error', {'message': 'Room name is required'})
        return
    
    room_id = str(uuid.uuid4())[:8]
    
    try:
        db_create_room(room_id, room_name, '', room_type, username)
    except Exception as e:
        emit('room_created_error', {'message': 'Database error: ' + str(e)})
        return
    
    if username in active_users:
        join_room(room_id)
    
    room = db_get_room(room_id)
    emit('room_created', {'room': room})
    socketio.emit('room_list', db_get_rooms(), broadcast=True)

# Friend events
@socketio.on('send_friend_request')
def handle_send_friend_request(data):
    if request.sid not in socket_sessions:
        emit('session_expired', {'message': 'Please login again'})
        return
    
    session = socket_sessions[request.sid]
    from_user = session['username']
    to_user = data.get('to', '').strip()
    
    if not to_user:
        emit('friend_request_error', {'message': 'Username required'})
        return
    
    if from_user == to_user:
        emit('friend_request_error', {'message': 'Cannot add yourself'})
        return
    
    # Check if user exists
    if not db_get_user_by_username(to_user):
        emit('friend_request_error', {'message': 'User not found'})
        return
    
    # Check if already friends
    if are_friends(from_user, to_user):
        emit('friend_request_error', {'message': 'Already friends'})
        return
    
    # Send friend request
    if not db_add_friend_request(from_user, to_user):
        emit('friend_request_error', {'message': 'Failed to send friend request'})
        return
    
    # Notify recipient if online
    if to_user in active_users:
        socketio.emit('friend_request_received', {
            'from': from_user
        }, room=active_users[to_user])
    
    emit('friend_request_sent', {'success': True})

@socketio.on('get_friends')
def handle_get_friends(data):
    if request.sid not in socket_sessions:
        return
    
    session = socket_sessions[request.sid]
    username = session['username']
    
    friends = db_get_friends(username)
    friends_list = []
    for friend in friends:
        is_connected = friend in active_users
        friends_list.append({
            'username': friend,
            'connected': is_connected
        })
    
    emit('friends_list', {'friends': friends_list})

# Initialize database
with app.app_context():
    init_db()

# ==================== MAIN ENTRY POINT ====================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'false').lower() == 'true'
    
    print("=" * 70)
    print("🚀 ECHOROOM - Railway.com Deployment Ready")
    print("=" * 70)
    print(f"📊 Database: {DATABASE}")
    print(f"🌐 Port: {port}")
    print(f"🔧 Debug: {debug}")
    print(f"📧 Email: {'Configured' if EMAIL_SENDER and EMAIL_PASSWORD else 'Not configured'}")
    print("\n✅ Endpoints:")
    print(f"   - Health: http://localhost:{port}/health")
    print(f"   - Stats: http://localhost:{port}/stats")
    print("\n🔑 Premium Code: 'The Goat'")
    print("=" * 70)
    
    socketio.run(app, 
                 host='0.0.0.0', 
                 port=port, 
                 debug=debug)

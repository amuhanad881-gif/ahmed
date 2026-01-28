#!/usr/bin/env python3
"""
Accounts Management Module
Handles user registration, authentication, and account data
"""

import json
import os
import hashlib
import secrets
from datetime import datetime, timedelta

# ==================== FILE PATHS ====================
ACCOUNTS_FILE = 'accounts_data.json'

# ==================== HELPER FUNCTIONS ====================

def hash_password(password, salt=None):
    """Hash password with salt"""
    if salt is None:
        salt = secrets.token_hex(16)
    return hashlib.sha256((password + salt).encode()).hexdigest(), salt

def verify_password(password, hashed_password, salt):
    """Verify password against stored hash"""
    return hashlib.sha256((password + salt).encode()).hexdigest() == hashed_password

# ==================== DATA MANAGEMENT ====================

def load_accounts():
    """Load accounts from file"""
    try:
        if os.path.exists(ACCOUNTS_FILE):
            with open(ACCOUNTS_FILE, 'r') as f:
                return json.load(f)
        else:
            print(f"📁 Creating new accounts file: {ACCOUNTS_FILE}")
    except Exception as e:
        print(f"❌ Error loading accounts: {e}")
    
    return {
        'users': {},  # email -> user data
        'sessions': {}  # email -> sessions list
    }

def save_accounts(accounts_data):
    """Save accounts to file"""
    try:
        with open(ACCOUNTS_FILE, 'w') as f:
            json.dump(accounts_data, f, indent=2)
        print(f"💾 Accounts saved to {ACCOUNTS_FILE}")
        return True
    except Exception as e:
        print(f"❌ Error saving accounts: {e}")
        return False

# ==================== ACCOUNT OPERATIONS ====================

def create_account(email, username, password):
    """
    Create a new user account
    Returns: (success, message, user_data)
    """
    accounts = load_accounts()
    
    # Check if email already exists
    if email in accounts['users']:
        return False, 'Email already registered', None
    
    # Check if username already exists
    for user_data in accounts['users'].values():
        if user_data.get('username') == username:
            return False, 'Username already taken', None
    
    # Hash password
    hashed_password, salt = hash_password(password)
    
    # Create user data
    user_data = {
        'username': username,
        'email': email,
        'password_hash': hashed_password,
        'salt': salt,
        'premium': False,
        'created_at': datetime.now().isoformat(),
        'verified': False,
        'last_login': None
    }
    
    # Save to accounts
    accounts['users'][email] = user_data
    accounts['sessions'][email] = []
    
    save_accounts(accounts)
    
    print(f"✅ Account created: {username} ({email})")
    return True, 'Account created successfully', user_data

def authenticate_user(email, password):
    """
    Authenticate user with email and password
    Returns: (success, message, user_data)
    """
    accounts = load_accounts()
    
    if email not in accounts['users']:
        return False, 'Invalid email or password', None
    
    user_data = accounts['users'][email]
    
    # Verify password
    if not verify_password(password, user_data['password_hash'], user_data['salt']):
        return False, 'Invalid email or password', None
    
    # Update last login
    user_data['last_login'] = datetime.now().isoformat()
    accounts['users'][email] = user_data
    save_accounts(accounts)
    
    print(f"✅ User authenticated: {user_data['username']} ({email})")
    return True, 'Login successful', user_data

def get_user_by_email(email):
    """Get user data by email"""
    accounts = load_accounts()
    return accounts['users'].get(email)

def get_user_by_username(username):
    """Get user data by username"""
    accounts = load_accounts()
    for email, user_data in accounts['users'].items():
        if user_data.get('username') == username:
            return user_data
    return None

def update_user_data(email, updates):
    """Update user data"""
    accounts = load_accounts()
    
    if email not in accounts['users']:
        return False, 'User not found'
    
    accounts['users'][email].update(updates)
    save_accounts(accounts)
    
    print(f"✅ User data updated: {email}")
    return True, 'User updated successfully'

def change_user_password(email, current_password, new_password):
    """Change user password"""
    accounts = load_accounts()
    
    if email not in accounts['users']:
        return False, 'User not found'
    
    user_data = accounts['users'][email]
    
    # Verify current password
    if not verify_password(current_password, user_data['password_hash'], user_data['salt']):
        return False, 'Current password is incorrect'
    
    # Hash new password
    hashed_password, salt = hash_password(new_password)
    
    # Update password
    accounts['users'][email]['password_hash'] = hashed_password
    accounts['users'][email]['salt'] = salt
    
    save_accounts(accounts)
    
    print(f"✅ Password changed: {email}")
    return True, 'Password changed successfully'

def activate_premium(email, duration_days=30):
    """Activate premium for user"""
    accounts = load_accounts()
    
    if email not in accounts['users']:
        return False, 'User not found'
    
    accounts['users'][email]['premium'] = True
    accounts['users'][email]['premium_until'] = (
        datetime.now() + timedelta(days=duration_days)
    ).isoformat()
    
    save_accounts(accounts)
    
    print(f"✅ Premium activated: {email} for {duration_days} days")
    return True, f'Premium activated for {duration_days} days'

def get_all_users():
    """Get all users (for admin purposes)"""
    accounts = load_accounts()
    return accounts['users']

def get_user_count():
    """Get total number of registered users"""
    accounts = load_accounts()
    return len(accounts['users'])

# ==================== SESSION MANAGEMENT ====================

def create_session(email, token):
    """Create a new session for user"""
    accounts = load_accounts()
    
    if email not in accounts['sessions']:
        accounts['sessions'][email] = []
    
    expiry = datetime.now() + timedelta(days=30)
    
    session_data = {
        'token': token,
        'created_at': datetime.now().isoformat(),
        'expires_at': expiry.isoformat()
    }
    
    accounts['sessions'][email].append(session_data)
    
    # Keep only last 5 sessions
    if len(accounts['sessions'][email]) > 5:
        accounts['sessions'][email] = accounts['sessions'][email][-5:]
    
    save_accounts(accounts)
    return True

def validate_session(email, token):
    """Validate user session token"""
    accounts = load_accounts()
    
    if email not in accounts['sessions']:
        return False
    
    now = datetime.now()
    valid_sessions = []
    is_valid = False
    
    for session in accounts['sessions'][email]:
        expiry = datetime.fromisoformat(session['expires_at'])
        if expiry > now:
            valid_sessions.append(session)
            if session['token'] == token:
                is_valid = True
    
    # Remove expired sessions
    accounts['sessions'][email] = valid_sessions
    save_accounts(accounts)
    
    return is_valid

def invalidate_all_sessions(email):
    """Invalidate all sessions for a user"""
    accounts = load_accounts()
    
    if email in accounts['sessions']:
        accounts['sessions'][email] = []
        save_accounts(accounts)
        return True
    return False
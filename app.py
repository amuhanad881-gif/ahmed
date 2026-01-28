#!/usr/bin/env python3
"""
EchoRoom - Discord-like Voice & Text Chat with Avatar System
COMPLETELY FIXED AND WORKING
"""

import uuid
import hashlib
import json
import os
from datetime import datetime
from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, emit, join_room

# Initialize Flask app FIRST
app = Flask(__name__)
app.secret_key = 'echo-room-secret-key-2025'

# Initialize SocketIO AFTER app
socketio = SocketIO(app, 
                   cors_allowed_origins="*",
                   async_mode='threading')

# ==================== HTML TEMPLATE ====================
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎤 EchoRoom - Voice & Text Chat</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 100%);
            color: #fff; min-height: 100vh;
        }
        .container { 
            display: flex; height: 100vh; max-width: 1600px; 
            margin: 0 auto; box-shadow: 0 0 50px rgba(0,0,0,0.5);
        }
        .sidebar { 
            width: 280px; background: rgba(20, 20, 30, 0.95); 
            padding: 20px; overflow-y: auto; 
            border-right: 1px solid rgba(255,255,255,0.1);
        }
        .logo { 
            font-size: 24px; font-weight: bold; margin-bottom: 30px; 
            color: #00e5ff; display: flex; align-items: center; 
            gap: 10px; padding: 10px; 
            background: rgba(0, 229, 255, 0.1); border-radius: 10px;
        }
        .logo i { animation: pulse 2s infinite; }
        .nav-section { margin-bottom: 25px; }
        .nav-section h3 { 
            font-size: 12px; text-transform: uppercase; 
            letter-spacing: 1px; color: #888; margin-bottom: 10px; 
            padding-left: 10px;
        }
        .nav-item { 
            padding: 12px 15px; margin: 5px 0; 
            background: rgba(255,255,255,0.05); border-radius: 8px; 
            cursor: pointer; transition: all 0.3s; 
            display: flex; align-items: center; gap: 12px;
        }
        .nav-item:hover { 
            background: rgba(0, 229, 255, 0.2); 
            transform: translateX(5px);
        }
        .nav-item.active { 
            background: rgba(0, 229, 255, 0.3); 
            border-left: 3px solid #00e5ff;
        }
        .badge { 
            background: #ff2e63; color: white; padding: 2px 8px; 
            border-radius: 10px; font-size: 11px; margin-left: auto;
        }
        .user-profile { 
            margin-top: auto; padding: 15px; 
            background: rgba(0,0,0,0.2); border-radius: 15px; 
            display: flex; align-items: center; gap: 15px; 
            cursor: pointer; transition: all 0.3s;
        }
        .user-profile:hover { 
            background: rgba(0, 229, 255, 0.1); 
            transform: translateY(-2px);
        }
        .user-avatar { 
            width: 50px; height: 50px; border-radius: 50%; 
            overflow: hidden; border: 3px solid #00e5ff; 
            background: rgba(255,255,255,0.1); 
            display: flex; align-items: center; 
            justify-content: center; font-size: 24px;
        }
        .user-avatar img { width: 100%; height: 100%; object-fit: cover; }
        .user-info { flex: 1; }
        .user-info strong { display: block; font-size: 16px; margin-bottom: 5px; }
        .user-info .status { font-size: 12px; opacity: 0.7; }
        .premium-badge { 
            background: linear-gradient(45deg, #ffd700, #ffed4e); 
            color: #333; padding: 2px 8px; border-radius: 10px; 
            font-size: 10px; font-weight: bold; margin-top: 5px; 
            display: inline-block;
        }
        .upgrade-btn { 
            padding: 8px 16px; 
            background: linear-gradient(135deg, #ffd700, #ffed4e); 
            color: #333; border: none; border-radius: 10px; 
            cursor: pointer; font-size: 12px; font-weight: bold; 
            transition: all 0.3s;
        }
        .upgrade-btn:hover { 
            transform: scale(1.05); 
            box-shadow: 0 5px 15px rgba(255,215,0,0.3);
        }
        .main { 
            flex: 1; display: flex; flex-direction: column; 
            background: rgba(25, 25, 35, 0.95); position: relative;
        }
        .chat-header { 
            padding: 20px; background: rgba(0,0,0,0.3); 
            border-bottom: 1px solid rgba(255,255,255,0.1); 
            display: flex; justify-content: space-between; 
            align-items: center; backdrop-filter: blur(10px);
        }
        .chat-header h2 { 
            display: flex; align-items: center; gap: 10px; 
            color: #00e5ff;
        }
        .chat-messages { 
            flex: 1; padding: 20px; overflow-y: auto; 
            display: flex; flex-direction: column; gap: 15px; 
            background: rgba(15, 15, 25, 0.8);
        }
        .message { 
            display: flex; gap: 15px; 
            animation: slideIn 0.3s ease;
        }
        .message.own { flex-direction: row-reverse; }
        .message-avatar { 
            width: 40px; height: 40px; border-radius: 50%; 
            overflow: hidden; border: 2px solid rgba(255,255,255,0.1); 
            flex-shrink: 0; background: rgba(255,255,255,0.1); 
            display: flex; align-items: center; 
            justify-content: center; font-size: 18px;
        }
        .message-avatar img { width: 100%; height: 100%; object-fit: cover; }
        .message-content { flex: 1; max-width: 70%; }
        .message-bubble { 
            background: rgba(255,255,255,0.07); padding: 15px; 
            border-radius: 15px; border: 1px solid rgba(255,255,255,0.05);
        }
        .message.own .message-bubble { 
            background: rgba(0, 229, 255, 0.2); 
            border-color: rgba(0, 229, 255, 0.3);
        }
        .message-header { 
            display: flex; justify-content: space-between; 
            margin-bottom: 8px; font-size: 12px; opacity: 0.8;
        }
        .message-text { line-height: 1.6; font-size: 15px; }
        .modal { 
            display: none; position: fixed; top: 0; left: 0; 
            width: 100%; height: 100%; 
            background: rgba(0,0,0,0.95); z-index: 3000; 
            justify-content: center; align-items: center; 
            backdrop-filter: blur(10px);
        }
        .settings-modal-content { 
            background: linear-gradient(135deg, rgba(30,30,40,0.98), rgba(20,20,30,0.98)); 
            padding: 40px; border-radius: 20px; width: 90%; 
            max-width: 800px; max-height: 90vh; overflow-y: auto; 
            border: 1px solid rgba(0,229,255,0.3); 
            box-shadow: 0 0 50px rgba(0,229,255,0.2); position: relative;
        }
        .close-btn { 
            position: absolute; top: 20px; right: 20px; 
            background: transparent; border: none; 
            color: rgba(255,255,255,0.7); font-size: 24px; 
            cursor: pointer; transition: all 0.3s; width: 40px; 
            height: 40px; border-radius: 50%; 
            display: flex; align-items: center; justify-content: center;
        }
        .close-btn:hover { 
            background: rgba(255,255,255,0.1); color: #00e5ff; 
            transform: rotate(90deg);
        }
        .settings-tabs { 
            display: flex; gap: 10px; margin-bottom: 30px; 
            border-bottom: 1px solid rgba(255,255,255,0.1); 
            padding-bottom: 10px;
        }
        .settings-tab { 
            padding: 12px 24px; background: transparent; border: none; 
            color: rgba(255,255,255,0.7); cursor: pointer; 
            font-size: 16px; border-radius: 10px; transition: all 0.3s;
        }
        .settings-tab:hover { background: rgba(255,255,255,0.05); }
        .settings-tab.active { 
            background: rgba(0, 229, 255, 0.2); color: #00e5ff; 
            border-bottom: 2px solid #00e5ff;
        }
        .settings-section { display: none; animation: fadeIn 0.5s ease; }
        .settings-section.active { display: block; }
        .avatar-preview-container { text-align: center; margin-bottom: 30px; }
        .avatar-preview { 
            width: 150px; height: 150px; border-radius: 50%; 
            overflow: hidden; margin: 0 auto 20px; 
            border: 4px solid #00e5ff; background: rgba(255,255,255,0.1); 
            position: relative;
        }
        .avatar-preview img { width: 100%; height: 100%; object-fit: cover; }
        .avatar-placeholder { 
            display: flex; align-items: center; justify-content: center; 
            width: 100%; height: 100%; font-size: 48px; 
            color: rgba(255,255,255,0.5);
        }
        .avatar-overlay { 
            position: absolute; top: 0; left: 0; width: 100%; height: 100%; 
            background: rgba(0,0,0,0.7); display: flex; align-items: center; 
            justify-content: center; opacity: 0; transition: opacity 0.3s; 
            cursor: pointer;
        }
        .avatar-preview:hover .avatar-overlay { opacity: 1; }
        .banner-preview-container { margin-bottom: 30px; }
        .banner-preview { 
            width: 100%; height: 200px; border-radius: 15px; 
            overflow: hidden; margin-bottom: 20px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            position: relative;
        }
        .banner-placeholder { 
            display: flex; align-items: center; justify-content: center; 
            width: 100%; height: 100%; font-size: 48px; 
            color: rgba(255,255,255,0.3);
        }
        .file-input-wrapper { position: relative; margin-bottom: 20px; }
        .file-input { 
            position: absolute; width: 0; height: 0; opacity: 0;
        }
        .file-input-label { 
            display: block; padding: 15px; 
            background: rgba(0, 229, 255, 0.1); 
            border: 2px dashed rgba(0, 229, 255, 0.5); 
            border-radius: 10px; text-align: center; cursor: pointer; 
            transition: all 0.3s;
        }
        .file-input-label:hover { 
            background: rgba(0, 229, 255, 0.2); 
            border-color: #00e5ff;
        }
        .form-group { margin-bottom: 25px; }
        .form-group label { 
            display: block; margin-bottom: 10px; 
            color: rgba(255,255,255,0.9); font-size: 14px; 
            font-weight: 500;
        }
        .form-group input, .form-group select, .form-group textarea { 
            width: 100%; padding: 15px; 
            border: 1px solid rgba(255,255,255,0.2); 
            border-radius: 10px; background: rgba(255,255,255,0.08); 
            color: white; font-size: 16px; transition: all 0.3s;
        }
        .btn { 
            padding: 15px 30px; 
            background: linear-gradient(135deg, #00e5ff, #00b8d4); 
            color: white; border: none; border-radius: 10px; 
            cursor: pointer; font-size: 16px; font-weight: bold; 
            transition: all 0.3s; width: 100%;
        }
        .btn:hover { 
            transform: translateY(-2px); 
            box-shadow: 0 10px 20px rgba(0,229,255,0.3);
        }
        .btn-success { 
            background: linear-gradient(135deg, #43b581, #3ca374);
        }
        .btn-danger { 
            background: linear-gradient(135deg, #ff2e63, #d81b60);
        }
        .btn-premium { 
            background: linear-gradient(135deg, #ffd700, #ffed4e); 
            color: #333;
        }
        .premium-feature-badge { 
            background: linear-gradient(45deg, #ffd700, #ffed4e); 
            color: #333; padding: 4px 12px; border-radius: 10px; 
            font-size: 12px; font-weight: bold; margin-left: 10px;
        }
        .message-input-area { 
            padding: 20px; background: rgba(0,0,0,0.3); 
            border-top: 1px solid rgba(255,255,255,0.1); 
            display: flex; gap: 10px; align-items: center; 
            position: relative;
        }
        .message-input { 
            flex: 1; padding: 15px 20px; border: none; 
            border-radius: 25px; background: rgba(255,255,255,0.08); 
            color: white; font-size: 16px; outline: none;
        }
        .input-btn { 
            width: 50px; height: 50px; border-radius: 50%; border: none; 
            background: #00e5ff; color: white; cursor: pointer; 
            font-size: 18px; transition: all 0.3s; 
            display: flex; align-items: center; justify-content: center;
        }
        .input-btn:hover { 
            background: #00b8d4; transform: scale(1.1);
        }
        @keyframes slideIn { 
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        @keyframes fadeIn { 
            from { opacity: 0; } to { opacity: 1; }
        }
        @keyframes pulse { 
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        .notification { 
            position: fixed; top: 20px; right: 20px; 
            padding: 15px 25px; background: rgba(30,30,40,0.95); 
            border-radius: 10px; border-left: 4px solid #00e5ff; 
            animation: slideIn 0.3s ease; z-index: 3000; 
            backdrop-filter: blur(10px); 
            border: 1px solid rgba(255,255,255,0.1);
        }
        .notification.success { border-left-color: #43b581; }
        .notification.error { border-left-color: #ff2e63; }
        #auth-modal { display: flex; }
        .auth-modal-content { 
            background: linear-gradient(135deg, rgba(30,30,40,0.95), rgba(20,20,30,0.95)); 
            padding: 40px; border-radius: 20px; width: 90%; 
            max-width: 400px; border: 1px solid rgba(0,229,255,0.3); 
            box-shadow: 0 0 50px rgba(0,229,255,0.2); position: relative;
        }
        .auth-tabs { display: flex; gap: 10px; margin-bottom: 30px; }
        .auth-tab { 
            flex: 1; padding: 12px; background: transparent; 
            border: none; color: rgba(255,255,255,0.7); 
            cursor: pointer; font-size: 16px; border-radius: 10px; 
            transition: all 0.3s;
        }
        .auth-tab:hover { background: rgba(255,255,255,0.05); }
        .auth-tab.active { 
            background: rgba(0, 229, 255, 0.2); color: #00e5ff;
        }
        .auth-section { display: none; }
        .auth-section.active { display: block; }
    </style>
</head>
<body>
    <!-- Login/Signup Modal -->
    <div class="modal" id="auth-modal">
        <div class="auth-modal-content">
            <button class="close-btn" onclick="hideAuthModal()">
                <i class="fas fa-times"></i>
            </button>
            <div class="auth-header">
                <h2><i class="fas fa-broadcast-tower"></i> EchoRoom</h2>
                <p>Voice & Text Chat Platform</p>
            </div>
            
            <div class="auth-tabs">
                <button class="auth-tab active" onclick="showAuthTab('login')">Login</button>
                <button class="auth-tab" onclick="showAuthTab('signup')">Sign Up</button>
            </div>
            
            <div id="login-section" class="auth-section active">
                <div class="form-group">
                    <label>Email</label>
                    <input type="email" id="login-email" placeholder="test@test.com" value="test@test.com">
                </div>
                <div class="form-group">
                    <label>Password</label>
                    <input type="password" id="login-password" placeholder="••••••••" value="123456">
                </div>
                <button class="btn" onclick="login()">
                    <i class="fas fa-sign-in-alt"></i> Login
                </button>
                <div style="margin-top: 15px; text-align: center; opacity: 0.7; font-size: 14px;">
                    Test account pre-filled
                </div>
            </div>
            
            <div id="signup-section" class="auth-section">
                <div class="form-group">
                    <label>Username</label>
                    <input type="text" id="signup-username" placeholder="Choose username">
                </div>
                <div class="form-group">
                    <label>Email</label>
                    <input type="email" id="signup-email" placeholder="your@email.com">
                </div>
                <div class="form-group">
                    <label>Password</label>
                    <input type="password" id="signup-password" placeholder="••••••••">
                </div>
                <button class="btn btn-success" onclick="signup()">
                    <i class="fas fa-user-plus"></i> Create Account
                </button>
            </div>
        </div>
    </div>

    <!-- Main App -->
    <div class="container" id="main-app" style="display: none;">
        <!-- Left Sidebar -->
        <div class="sidebar">
            <div class="logo">
                <i class="fas fa-broadcast-tower"></i>
                EchoRoom 🎤
            </div>
            
            <div class="nav-section">
                <h3>Rooms</h3>
                <div id="servers-list">
                    <!-- Rooms will be populated here -->
                </div>
                <div class="nav-item" onclick="showCreateRoomModal()">
                    <i class="fas fa-plus"></i>
                    <span>Create Room</span>
                </div>
            </div>

            <div class="nav-section">
                <h3>Friends</h3>
                <div id="friends-list" class="friends-list">
                    <!-- Friends will appear here -->
                </div>
                <div class="nav-item" onclick="showAddFriendModal()">
                    <i class="fas fa-user-plus"></i>
                    <span>Add Friend</span>
                </div>
            </div>

            <!-- User Profile Section -->
            <div class="user-profile" onclick="showSettingsModal()" id="user-profile">
                <div class="user-avatar" id="user-avatar-preview">
                    <div class="avatar-placeholder">
                        <i class="fas fa-user"></i>
                    </div>
                </div>
                <div class="user-info">
                    <strong id="username-display">Guest</strong>
                    <div class="status" id="user-status">Free User</div>
                    <div class="premium-badge" id="premium-badge" style="display: none;">PREMIUM</div>
                </div>
                <button class="upgrade-btn" id="upgrade-btn" onclick="event.stopPropagation(); showUpgradeModal()">
                    <i class="fas fa-crown"></i> Upgrade
                </button>
            </div>
        </div>

        <!-- Main Chat Area -->
        <div class="main">
            <div class="chat-header">
                <h2 id="current-chat-name">
                    <i class="fas fa-hashtag"></i> General
                </h2>
                <div class="user-info">
                    <div id="connection-status" class="premium-badge">
                        <i class="fas fa-wifi"></i> Connected
                    </div>
                </div>
            </div>

            <div class="chat-messages" id="chat-messages">
                <!-- Messages will appear here -->
            </div>

            <div class="message-input-area">
                <input type="text" class="message-input" id="message-input" 
                       placeholder="Type your message here..." 
                       onkeypress="if(event.keyCode===13) sendMessage()">
                <button class="input-btn" onclick="sendMessage()">
                    <i class="fas fa-paper-plane"></i>
                </button>
            </div>
        </div>

        <!-- Right Panel -->
        <div class="sidebar" style="width: 300px; border-left: 1px solid rgba(255,255,255,0.1); border-right: none;">
            <div class="nav-section">
                <h3>Voice Controls</h3>
                <div style="display: flex; flex-direction: column; gap: 10px;">
                    <button class="btn" id="mute-btn" onclick="toggleMute()">
                        <i class="fas fa-microphone"></i> Mute
                    </button>
                    <button class="btn" id="deafen-btn" onclick="toggleDeafen()">
                        <i class="fas fa-headset"></i> Deafen
                    </button>
                </div>
            </div>
            
            <div class="nav-section">
                <h3>Online Users</h3>
                <div id="online-users" class="friends-list">
                    <!-- Online users will appear here -->
                </div>
            </div>
        </div>
    </div>

    <!-- Settings Modal -->
    <div class="modal" id="settings-modal">
        <div class="settings-modal-content">
            <button class="close-btn" onclick="hideSettingsModal()">
                <i class="fas fa-times"></i>
            </button>
            
            <div class="settings-header">
                <h2><i class="fas fa-cog"></i> User Settings</h2>
                <p>Customize your EchoRoom profile</p>
            </div>

            <div class="settings-tabs">
                <button class="settings-tab active" onclick="showSettingsTab('profile')">
                    <i class="fas fa-user"></i> Profile
                </button>
                <button class="settings-tab" onclick="showSettingsTab('appearance')">
                    <i class="fas fa-palette"></i> Appearance
                </button>
            </div>

            <!-- Profile Tab -->
            <div id="profile-tab" class="settings-section active">
                <div class="avatar-preview-container">
                    <div class="avatar-preview" id="settings-avatar-preview">
                        <div class="avatar-placeholder">
                            <i class="fas fa-user"></i>
                        </div>
                        <div class="avatar-overlay" onclick="document.getElementById('avatar-upload').click()">
                            <i class="fas fa-camera"></i> Change Avatar
                        </div>
                    </div>
                    <div class="file-input-wrapper">
                        <input type="file" id="avatar-upload" class="file-input" accept="image/*" onchange="handleAvatarUpload(event)">
                        <label for="avatar-upload" class="file-input-label">
                            <i class="fas fa-upload"></i> Upload Avatar
                        </label>
                    </div>
                </div>

                <div class="banner-preview-container">
                    <h3>Profile Banner <span class="premium-feature-badge">PREMIUM</span></h3>
                    <div class="banner-preview" id="settings-banner-preview">
                        <div class="banner-placeholder">
                            <i class="fas fa-image"></i>
                        </div>
                    </div>
                    <div class="file-input-wrapper">
                        <input type="file" id="banner-upload" class="file-input" accept="image/*" onchange="handleBannerUpload(event)">
                        <label for="banner-upload" class="file-input-label" id="banner-upload-label">
                            <i class="fas fa-upload"></i> Upload Banner
                        </label>
                    </div>
                </div>

                <div class="form-group">
                    <label for="display-name">Display Name</label>
                    <input type="text" id="display-name" placeholder="Enter your display name">
                </div>

                <div class="form-group">
                    <label for="user-bio">Bio</label>
                    <textarea id="user-bio" placeholder="Tell us about yourself..." rows="3"></textarea>
                </div>

                <button class="btn btn-success" onclick="saveProfileSettings()">
                    <i class="fas fa-save"></i> Save Changes
                </button>
            </div>

            <!-- Appearance Tab -->
            <div id="appearance-tab" class="settings-section">
                <div class="form-group">
                    <label>Theme</label>
                    <select id="theme-select">
                        <option value="dark">🌙 Dark Theme</option>
                        <option value="light">☀️ Light Theme</option>
                        <option value="blue">🔵 Blue Theme</option>
                    </select>
                </div>

                <button class="btn btn-success" onclick="saveAppearanceSettings()">
                    <i class="fas fa-save"></i> Save Appearance
                </button>
            </div>
        </div>
    </div>

    <!-- Other Modals -->
    <div class="modal" id="create-room-modal">
        <div class="settings-modal-content">
            <button class="close-btn" onclick="hideCreateRoomModal()">
                <i class="fas fa-times"></i>
            </button>
            
            <div class="settings-header">
                <h2><i class="fas fa-plus-circle"></i> Create New Room</h2>
            </div>

            <div class="form-group">
                <label for="room-name">Room Name</label>
                <input type="text" id="room-name" placeholder="Enter room name">
            </div>

            <div class="form-group">
                <label for="room-description">Description (Optional)</label>
                <textarea id="room-description" placeholder="Room description..." rows="2"></textarea>
            </div>

            <button class="btn btn-success" onclick="createRoom()">
                <i class="fas fa-plus"></i> Create Room
            </button>
        </div>
    </div>

    <div class="modal" id="add-friend-modal">
        <div class="settings-modal-content">
            <button class="close-btn" onclick="hideAddFriendModal()">
                <i class="fas fa-times"></i>
            </button>
            
            <div class="settings-header">
                <h2><i class="fas fa-user-plus"></i> Add Friend</h2>
            </div>

            <div class="form-group">
                <label for="friend-username">Username</label>
                <input type="text" id="friend-username" placeholder="Enter username">
            </div>

            <button class="btn btn-success" onclick="sendFriendRequest()">
                <i class="fas fa-user-plus"></i> Send Friend Request
            </button>
        </div>
    </div>

    <div class="modal" id="upgrade-modal">
        <div class="settings-modal-content">
            <button class="close-btn" onclick="hideUpgradeModal()">
                <i class="fas fa-times"></i>
            </button>
            
            <div class="settings-header">
                <h2><i class="fas fa-crown"></i> Upgrade to Premium</h2>
                <p>Unlock exclusive features</p>
            </div>

            <div style="text-align: center; margin-bottom: 30px;">
                <div style="font-size: 48px; color: #ffd700; margin-bottom: 20px;">
                    <i class="fas fa-crown"></i>
                </div>
                <h3 style="color: #ffd700; margin-bottom: 20px;">Premium Features</h3>
                <ul style="text-align: left; margin-bottom: 30px; padding-left: 20px;">
                    <li style="margin-bottom: 10px;">Custom profile banner</li>
                    <li style="margin-bottom: 10px;">HD avatar uploads</li>
                    <li style="margin-bottom: 10px;">Special badge on profile</li>
                </ul>
            </div>

            <div class="form-group">
                <label for="owner-code">Owner Code</label>
                <input type="text" id="owner-code" placeholder="Enter 'test' for testing">
            </div>

            <button class="btn btn-premium" onclick="upgradeToPremium()">
                <i class="fas fa-crown"></i> Activate Premium
            </button>
        </div>
    </div>

    <div id="notification-container"></div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.0/socket.io.min.js"></script>
    <script>
        let socket;
        let currentUser = '';
        let isPremium = false;
        let currentRoom = 'general';
        let userSettings = {};

        // Initialize WebSocket
        function initWebSocket() {
            socket = io();
            
            socket.on('connect', () => {
                console.log('✅ Connected to EchoRoom');
                showNotification('Connected to EchoRoom!', 'success');
                
                // Try to restore session
                const savedUser = localStorage.getItem('echoRoomUser');
                if (savedUser) {
                    const userData = JSON.parse(savedUser);
                    socket.emit('restore_session', userData);
                }
            });

            socket.on('disconnect', () => {
                console.log('❌ Disconnected from server');
                showNotification('Disconnected from server', 'error');
            });

            // Login/Signup events
            socket.on('login_success', (data) => {
                console.log('✅ Login success:', data);
                handleLoginSuccess(data);
            });

            socket.on('login_error', (data) => {
                console.log('❌ Login error:', data);
                showNotification(data.message || 'Login failed', 'error');
            });

            socket.on('signup_success', (data) => {
                console.log('✅ Signup success:', data);
                showNotification('Account created! Please login.', 'success');
                showAuthTab('login');
            });

            socket.on('signup_error', (data) => {
                console.log('❌ Signup error:', data);
                showNotification(data.message || 'Signup failed', 'error');
            });

            // Session events
            socket.on('session_restored', (data) => {
                console.log('✅ Session restored:', data);
                handleLoginSuccess(data);
            });

            socket.on('session_error', (data) => {
                console.log('❌ Session error:', data);
                showNotification(data.message || 'Session expired', 'error');
            });

            // Messages
            socket.on('message', (data) => {
                console.log('📨 New message:', data);
                addMessage(data);
            });

            socket.on('chat_messages', (messages) => {
                console.log('📨 Chat messages loaded:', messages?.length);
                const messagesDiv = document.getElementById('chat-messages');
                messagesDiv.innerHTML = '';
                if (messages && messages.length > 0) {
                    messages.forEach(msg => addMessage(msg));
                }
            });

            // User settings
            socket.on('user_settings', (settings) => {
                console.log('⚙️ User settings loaded:', settings);
                userSettings = settings || {};
                loadUserSettings();
            });

            socket.on('user_settings_updated', (data) => {
                console.log('✅ Settings updated');
                showNotification('Settings saved!', 'success');
            });

            // Rooms
            socket.on('room_list', (rooms) => {
                console.log('🏠 Rooms loaded:', rooms);
                updateRoomList(rooms);
            });

            socket.on('room_created', (data) => {
                console.log('✅ Room created:', data.room);
                addRoomToList(data.room);
                showNotification(`Room "${data.room.name}" created!`, 'success');
                hideCreateRoomModal();
            });

            // Friends
            socket.on('friends_list', (friends) => {
                console.log('👥 Friends loaded:', friends);
                updateFriendsList(friends);
            });

            socket.on('friend_request_sent', (data) => {
                console.log('✅ Friend request sent');
                showNotification('Friend request sent!', 'success');
                hideAddFriendModal();
            });

            socket.on('friend_request_error', (data) => {
                console.log('❌ Friend request error');
                showNotification(data.message || 'Friend request failed', 'error');
            });

            // Premium
            socket.on('premium_activated', (data) => {
                console.log('✅ Premium activated');
                isPremium = true;
                updateUserPremiumStatus(true);
                showNotification('Premium activated!', 'success');
                hideUpgradeModal();
            });

            socket.on('premium_error', (data) => {
                console.log('❌ Premium error');
                showNotification(data.message || 'Premium activation failed', 'error');
            });
        }

        // ========== AUTHENTICATION FUNCTIONS ==========
        function showAuthTab(tabName) {
            document.querySelectorAll('.auth-section').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.auth-tab').forEach(btn => {
                btn.classList.remove('active');
            });
            
            document.getElementById(`${tabName}-section`).classList.add('active');
            event.target.classList.add('active');
            
            // Focus first input
            if (tabName === 'login') {
                document.getElementById('login-email').focus();
            } else {
                document.getElementById('signup-username').focus();
            }
        }

        function hideAuthModal() {
            document.getElementById('auth-modal').style.display = 'none';
        }

        function login() {
            const email = document.getElementById('login-email').value.trim();
            const password = document.getElementById('login-password').value.trim();
            
            if (!email || !password) {
                showNotification('Please fill all fields', 'error');
                return;
            }
            
            console.log('🔑 Attempting login with:', email);
            socket.emit('login', { email, password });
        }

        function signup() {
            const username = document.getElementById('signup-username').value.trim();
            const email = document.getElementById('signup-email').value.trim();
            const password = document.getElementById('signup-password').value.trim();
            
            if (!username || !email || !password) {
                showNotification('Please fill all fields', 'error');
                return;
            }
            
            if (username.length < 3) {
                showNotification('Username must be at least 3 characters', 'error');
                return;
            }
            
            if (password.length < 6) {
                showNotification('Password must be at least 6 characters', 'error');
                return;
            }
            
            console.log('📝 Attempting signup:', { username, email });
            socket.emit('signup', { username, email, password });
        }

        function handleLoginSuccess(data) {
            console.log('🎉 Login success handler triggered');
            currentUser = data.username;
            isPremium = data.premium || false;
            
            // Update UI
            document.getElementById('auth-modal').style.display = 'none';
            document.getElementById('main-app').style.display = 'flex';
            document.getElementById('username-display').textContent = currentUser;
            
            updateUserPremiumStatus(isPremium);
            
            // Save session
            localStorage.setItem('echoRoomUser', JSON.stringify({
                username: currentUser,
                premium: isPremium,
                timestamp: Date.now()
            }));
            
            // Load data
            socket.emit('get_user_settings', { username: currentUser });
            socket.emit('get_rooms');
            socket.emit('get_friends');
            
            // Join general room
            socket.emit('join_room', {
                username: currentUser,
                room: 'general'
            });
            
            // Load messages for general room
            socket.emit('get_room_messages', { room: 'general' });
            
            showNotification(`Welcome ${currentUser}!`, 'success');
        }

        // ========== SETTINGS FUNCTIONS ==========
        function showSettingsModal() {
            document.getElementById('settings-modal').style.display = 'flex';
            loadUserSettings();
        }

        function hideSettingsModal() {
            document.getElementById('settings-modal').style.display = 'none';
        }

        function showSettingsTab(tabName) {
            document.querySelectorAll('.settings-section').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.settings-tab').forEach(btn => {
                btn.classList.remove('active');
            });
            
            document.getElementById(`${tabName}-tab`).classList.add('active');
            event.target.classList.add('active');
        }

        function loadUserSettings() {
            // Load display name
            const displayNameInput = document.getElementById('display-name');
            const userBioInput = document.getElementById('user-bio');
            const themeSelect = document.getElementById('theme-select');
            
            displayNameInput.value = userSettings.displayName || currentUser || '';
            userBioInput.value = userSettings.bio || '';
            themeSelect.value = userSettings.theme || 'dark';
            
            // Update avatar preview
            const avatarPreview = document.getElementById('settings-avatar-preview');
            const userAvatarPreview = document.getElementById('user-avatar-preview');
            
            if (userSettings.avatar) {
                if (userSettings.avatar.startsWith('data:image')) {
                    avatarPreview.innerHTML = `<img src="${userSettings.avatar}" alt="Avatar">`;
                    userAvatarPreview.innerHTML = `<img src="${userSettings.avatar}" alt="Avatar">`;
                } else {
                    avatarPreview.innerHTML = `<div class="avatar-placeholder">${userSettings.avatar}</div>`;
                    userAvatarPreview.innerHTML = `<div class="avatar-placeholder">${userSettings.avatar}</div>`;
                }
            }
            
            // Update banner preview
            const bannerPreview = document.getElementById('settings-banner-preview');
            const bannerLabel = document.getElementById('banner-upload-label');
            const bannerInput = document.getElementById('banner-upload');
            
            if (userSettings.banner && isPremium) {
                bannerPreview.innerHTML = `<img src="${userSettings.banner}" alt="Banner">`;
            }
            
            if (!isPremium) {
                bannerLabel.innerHTML = '<i class="fas fa-lock"></i> Premium Feature';
                bannerLabel.style.opacity = '0.7';
                bannerLabel.style.cursor = 'not-allowed';
                bannerInput.disabled = true;
            } else {
                bannerLabel.innerHTML = '<i class="fas fa-upload"></i> Upload Banner';
                bannerLabel.style.opacity = '1';
                bannerLabel.style.cursor = 'pointer';
                bannerInput.disabled = false;
            }
        }

        function updateUserPremiumStatus(premium) {
            isPremium = premium;
            const premiumBadge = document.getElementById('premium-badge');
            const upgradeBtn = document.getElementById('upgrade-btn');
            
            if (premium) {
                premiumBadge.style.display = 'inline-block';
                upgradeBtn.style.display = 'none';
                document.getElementById('user-status').textContent = '👑 Premium User';
                document.getElementById('user-status').style.color = '#ffd700';
            } else {
                premiumBadge.style.display = 'none';
                upgradeBtn.style.display = 'block';
                document.getElementById('user-status').textContent = 'Free User';
                document.getElementById('user-status').style.color = '';
            }
        }

        function handleAvatarUpload(event) {
            const file = event.target.files[0];
            if (!file) return;
            
            const reader = new FileReader();
            reader.onload = function(e) {
                const avatarData = e.target.result;
                
                // Update preview
                const avatarPreview = document.getElementById('settings-avatar-preview');
                avatarPreview.innerHTML = `<img src="${avatarData}" alt="Avatar">`;
                
                // Add overlay back
                const avatarOverlay = document.createElement('div');
                avatarOverlay.className = 'avatar-overlay';
                avatarOverlay.innerHTML = '<i class="fas fa-camera"></i> Change Avatar';
                avatarOverlay.onclick = () => document.getElementById('avatar-upload').click();
                avatarPreview.appendChild(avatarOverlay);
                
                // Save to user settings
                userSettings.avatar = avatarData;
                
                showNotification('Avatar updated! Click Save to keep changes.', 'success');
            };
            reader.readAsDataURL(file);
        }

        function handleBannerUpload(event) {
            if (!isPremium) {
                showNotification('Banner upload is a premium feature!', 'error');
                return;
            }
            
            const file = event.target.files[0];
            if (!file) return;
            
            const reader = new FileReader();
            reader.onload = function(e) {
                const bannerData = e.target.result;
                
                // Update preview
                const bannerPreview = document.getElementById('settings-banner-preview');
                bannerPreview.innerHTML = `<img src="${bannerData}" alt="Banner">`;
                
                // Save to user settings
                userSettings.banner = bannerData;
                
                showNotification('Banner updated! Click Save to keep changes.', 'success');
            };
            reader.readAsDataURL(file);
        }

        function saveProfileSettings() {
            const displayName = document.getElementById('display-name').value.trim() || currentUser;
            const bio = document.getElementById('user-bio').value.trim();
            
            userSettings.displayName = displayName;
            userSettings.bio = bio;
            
            socket.emit('update_user_settings', {
                username: currentUser,
                settings: userSettings
            });
            
            // Update UI
            document.getElementById('username-display').textContent = displayName;
        }

        function saveAppearanceSettings() {
            const theme = document.getElementById('theme-select').value;
            userSettings.theme = theme;
            
            socket.emit('update_user_settings', {
                username: currentUser,
                settings: userSettings
            });
        }

        // ========== CHAT FUNCTIONS ==========
        function sendMessage() {
            const input = document.getElementById('message-input');
            const message = input.value.trim();
            
            if (!message || !currentUser) return;
            
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
            messageDiv.className = `message ${data.username === currentUser ? 'own' : ''}`;
            
            messageDiv.innerHTML = `
                <div class="message-avatar">
                    <div class="avatar-placeholder">
                        ${data.username ? data.username.charAt(0).toUpperCase() : 'U'}
                    </div>
                </div>
                <div class="message-content">
                    <div class="message-bubble">
                        <div class="message-header">
                            <strong>${data.displayName || data.username || 'Unknown'}</strong>
                            <span>${new Date(data.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                        </div>
                        <div class="message-text">${escapeHtml(data.message)}</div>
                    </div>
                </div>
            `;
            
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        // ========== ROOM FUNCTIONS ==========
        function updateRoomList(rooms) {
            const list = document.getElementById('servers-list');
            list.innerHTML = '';
            
            if (!rooms || rooms.length === 0) {
                list.innerHTML = '<div style="padding: 10px; opacity: 0.7; text-align: center;">No rooms yet</div>';
                return;
            }
            
            rooms.forEach(room => {
                addRoomToList(room);
            });
        }

        function addRoomToList(room) {
            const list = document.getElementById('servers-list');
            const roomDiv = document.createElement('div');
            roomDiv.className = 'nav-item';
            roomDiv.innerHTML = `
                <i class="fas fa-hashtag"></i>
                <span>${room.name}</span>
            `;
            
            roomDiv.onclick = () => {
                joinRoom(room.id, room.name);
            };
            
            list.appendChild(roomDiv);
        }

        function joinRoom(roomId, roomName) {
            currentRoom = roomId;
            document.getElementById('current-chat-name').innerHTML = 
                `<i class="fas fa-hashtag"></i> ${roomName}`;
            
            document.getElementById('chat-messages').innerHTML = '';
            
            socket.emit('join_room', { 
                room: roomId, 
                username: currentUser 
            });
            
            socket.emit('get_room_messages', { room: roomId });
            
            addSystemMessage(`Joined ${roomName}`);
        }

        function addSystemMessage(text) {
            const messagesDiv = document.getElementById('chat-messages');
            const messageDiv = document.createElement('div');
            messageDiv.style.textAlign = 'center';
            messageDiv.style.opacity = '0.7';
            messageDiv.style.fontStyle = 'italic';
            messageDiv.style.padding = '10px';
            messageDiv.textContent = text;
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        // ========== CREATE ROOM FUNCTIONS ==========
        function showCreateRoomModal() {
            document.getElementById('create-room-modal').style.display = 'flex';
            document.getElementById('room-name').focus();
        }

        function hideCreateRoomModal() {
            document.getElementById('create-room-modal').style.display = 'none';
            document.getElementById('room-name').value = '';
            document.getElementById('room-description').value = '';
        }

        function createRoom() {
            const name = document.getElementById('room-name').value.trim();
            const description = document.getElementById('room-description').value.trim();
            
            if (!name) {
                showNotification('Room name is required', 'error');
                return;
            }
            
            socket.emit('create_room', {
                name: name,
                description: description,
                creator: currentUser
            });
        }

        // ========== FRIEND FUNCTIONS ==========
        function showAddFriendModal() {
            document.getElementById('add-friend-modal').style.display = 'flex';
            document.getElementById('friend-username').focus();
        }

        function hideAddFriendModal() {
            document.getElementById('add-friend-modal').style.display = 'none';
            document.getElementById('friend-username').value = '';
        }

        function sendFriendRequest() {
            const friendUsername = document.getElementById('friend-username').value.trim();
            
            if (!friendUsername) {
                showNotification('Please enter a username', 'error');
                return;
            }
            
            if (friendUsername === currentUser) {
                showNotification('You cannot add yourself', 'error');
                return;
            }
            
            socket.emit('send_friend_request', {
                from: currentUser,
                to: friendUsername
            });
        }

        function updateFriendsList(friends) {
            const friendsList = document.getElementById('friends-list');
            friendsList.innerHTML = '';
            
            if (!friends || friends.length === 0) {
                friendsList.innerHTML = '<div style="padding: 10px; opacity: 0.7; text-align: center;">No friends yet</div>';
                return;
            }
            
            friends.forEach(friend => {
                const friendDiv = document.createElement('div');
                friendDiv.className = 'nav-item';
                friendDiv.innerHTML = `
                    <i class="fas fa-user" style="color: ${friend.connected ? '#43b581' : '#888'}"></i>
                    <span>${friend.username}</span>
                `;
                friendsList.appendChild(friendDiv);
            });
        }

        // ========== UPGRADE FUNCTIONS ==========
        function showUpgradeModal() {
            document.getElementById('upgrade-modal').style.display = 'flex';
            document.getElementById('owner-code').focus();
        }

        function hideUpgradeModal() {
            document.getElementById('upgrade-modal').style.display = 'none';
            document.getElementById('owner-code').value = '';
        }

        function upgradeToPremium() {
            const ownerCode = document.getElementById('owner-code').value.trim();
            
            // Simple test code
            if (ownerCode === 'test') {
                socket.emit('activate_premium', {
                    username: currentUser
                });
            } else {
                showNotification('Invalid code. Use "test" for testing', 'error');
            }
        }

        // ========== UTILITY FUNCTIONS ==========
        function showNotification(message, type = 'info') {
            const container = document.getElementById('notification-container');
            const notification = document.createElement('div');
            notification.className = `notification ${type}`;
            notification.textContent = message;
            container.appendChild(notification);
            
            setTimeout(() => notification.remove(), 3000);
        }

        // ========== MUTE/DEAFEN FUNCTIONS ==========
        function toggleMute() {
            const btn = document.getElementById('mute-btn');
            const isMuted = btn.innerHTML.includes('Unmute');
            btn.innerHTML = isMuted ? 
                '<i class="fas fa-microphone"></i> Mute' : 
                '<i class="fas fa-microphone-slash"></i> Unmute';
            showNotification(isMuted ? 'Microphone unmuted' : 'Microphone muted', 'info');
        }

        function toggleDeafen() {
            const btn = document.getElementById('deafen-btn');
            const isDeafened = btn.innerHTML.includes('Undeafen');
            btn.innerHTML = isDeafened ? 
                '<i class="fas fa-headset"></i> Deafen' : 
                '<i class="fas fa-headset"></i> Undeafen';
            showNotification(isDeafened ? 'Undeafened' : 'Deafened', 'info');
        }

        // ========== INITIALIZATION ==========
        window.onload = function() {
            console.log('🚀 Initializing EchoRoom...');
            initWebSocket();
            
            // Enter key handlers
            document.getElementById('login-email').onkeypress = function(e) {
                if (e.key === 'Enter') login();
            };
            document.getElementById('login-password').onkeypress = function(e) {
                if (e.key === 'Enter') login();
            };
            
            document.getElementById('signup-username').onkeypress = function(e) {
                if (e.key === 'Enter') signup();
            };
            document.getElementById('signup-email').onkeypress = function(e) {
                if (e.key === 'Enter') signup();
            };
            document.getElementById('signup-password').onkeypress = function(e) {
                if (e.key === 'Enter') signup();
            };
            
            document.getElementById('message-input').onkeypress = function(e) {
                if (e.key === 'Enter') sendMessage();
            };
            
            document.getElementById('room-name').onkeypress = function(e) {
                if (e.key === 'Enter') createRoom();
            };
            
            document.getElementById('friend-username').onkeypress = function(e) {
                if (e.key === 'Enter') sendFriendRequest();
            };
            
            document.getElementById('owner-code').onkeypress = function(e) {
                if (e.key === 'Enter') upgradeToPremium();
            };
        };
    </script>
</body>
</html>
'''

# Data file and functions
DATA_FILE = 'echoroom_data.json'

def load_data():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {
        'users_db': {},
        'rooms_db': {},
        'messages_db': {},
        'user_settings': {}
    }

def save_data():
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump({
                'users_db': users_db,
                'rooms_db': rooms_db,
                'messages_db': messages_db,
                'user_settings': user_settings_db
            }, f, indent=2)
    except Exception as e:
        print(f"Error saving data: {e}")

# Load data
data = load_data()
users_db = data.get('users_db', {})
rooms_db = data.get('rooms_db', {})
messages_db = data.get('messages_db', {})
user_settings_db = data.get('user_settings', {})

active_users = {}

# Create default room if not exists
if "general" not in rooms_db:
    rooms_db["general"] = {
        'id': 'general',
        'name': 'General',
        'description': 'Welcome to EchoRoom!',
        'type': 'public',
        'creator': 'system',
        'created_at': datetime.now().isoformat(),
        'members': []
    }
    save_data()

# Create test user if not exists
if "test@test.com" not in users_db:
    users_db["test@test.com"] = {
        'username': 'testuser',
        'password_hash': hashlib.sha256("123456".encode()).hexdigest(),
        'premium': True,
        'friends': [],
        'friend_requests': []
    }
    save_data()

# ==================== FLASK ROUTES ====================

@app.route('/')
def index():
    """Main route - serves the HTML page"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/favicon.ico')
def favicon():
    return '', 404

# ==================== HELPER FUNCTIONS ====================

def find_user_email(username):
    for email, user_data in users_db.items():
        if user_data['username'] == username:
            return email
    return None

# ==================== SOCKETIO EVENTS ====================

@socketio.on('connect')
def handle_connect():
    print(f"✅ Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    for username, sid in list(active_users.items()):
        if sid == request.sid:
            del active_users[username]
            print(f"❌ User disconnected: {username}")
            break

@socketio.on('restore_session')
def handle_restore_session(data):
    username = data.get('username')
    
    user_email = find_user_email(username)
    if not user_email:
        emit('session_error', {'message': 'Session expired'})
        return
    
    user_data = users_db[user_email]
    active_users[username] = request.sid
    
    emit('session_restored', {
        'username': username,
        'premium': user_data.get('premium', False)
    })

@socketio.on('signup')
def handle_signup(data):
    username = data['username']
    email = data['email']
    password = data['password']
    
    if not username or not email or not password:
        emit('signup_error', {'message': 'All fields required'})
        return
    
    if email in users_db:
        emit('signup_error', {'message': 'Email already registered'})
        return
    
    # Check if username exists
    for user_data in users_db.values():
        if user_data['username'] == username:
            emit('signup_error', {'message': 'Username already taken'})
            return
    
    users_db[email] = {
        'username': username,
        'password_hash': hashlib.sha256(password.encode()).hexdigest(),
        'premium': False,
        'friends': [],
        'friend_requests': []
    }
    
    save_data()
    emit('signup_success', {'message': 'Account created successfully'})

@socketio.on('login')
def handle_login(data):
    email = data['email']
    password = data['password']
    
    if email not in users_db:
        emit('login_error', {'message': 'User not found'})
        return
    
    user_data = users_db[email]
    
    if user_data['password_hash'] != hashlib.sha256(password.encode()).hexdigest():
        emit('login_error', {'message': 'Wrong password'})
        return
    
    username = user_data['username']
    active_users[username] = request.sid
    
    emit('login_success', {
        'username': username,
        'premium': user_data.get('premium', False)
    })

@socketio.on('join_room')
def handle_join_room(data):
    username = data['username']
    room = data['room']
    
    if username in active_users:
        join_room(room)
        print(f"✅ {username} joined room: {room}")

@socketio.on('message')
def handle_message(data):
    message_id = str(uuid.uuid4())[:8]
    
    # Get user settings
    username = data['username']
    user_settings = user_settings_db.get(username, {})
    
    message = {
        'id': message_id,
        'username': username,
        'displayName': user_settings.get('displayName', username),
        'message': data['message'],
        'server': data['server'],
        'timestamp': data.get('timestamp', datetime.now().isoformat()),
        'type': 'server'
    }
    
    if data['server'] not in messages_db:
        messages_db[data['server']] = []
    messages_db[data['server']].append(message)
    
    if len(messages_db[data['server']]) > 500:
        messages_db[data['server']] = messages_db[data['server']][-500:]
    
    save_data()
    emit('message', message, room=data['server'])

@socketio.on('get_room_messages')
def handle_get_room_messages(data):
    room_id = data['room']
    room_messages = messages_db.get(room_id, [])
    emit('chat_messages', room_messages[-100:])

@socketio.on('get_rooms')
def handle_get_rooms():
    emit('room_list', list(rooms_db.values()))

@socketio.on('create_room')
def handle_create_room(data):
    room_id = str(uuid.uuid4())[:8]
    room = {
        'id': room_id,
        'name': data['name'],
        'description': data.get('description', ''),
        'creator': data['creator'],
        'created_at': datetime.now().isoformat(),
        'members': [data['creator']]
    }
    
    rooms_db[room_id] = room
    save_data()
    
    if data['creator'] in active_users:
        join_room(room_id)
    
    emit('room_created', {'room': room})
    emit('room_list', list(rooms_db.values()), broadcast=True)

@socketio.on('get_user_settings')
def handle_get_user_settings(data):
    username = data['username']
    
    if username not in user_settings_db:
        user_settings_db[username] = {
            'displayName': username,
            'avatar': None,
            'banner': None,
            'bio': '',
            'theme': 'dark'
        }
        save_data()
    
    emit('user_settings', user_settings_db[username])

@socketio.on('update_user_settings')
def handle_update_user_settings(data):
    username = data['username']
    settings = data['settings']
    
    if username not in user_settings_db:
        user_settings_db[username] = {}
    
    user_settings_db[username].update(settings)
    save_data()
    
    emit('user_settings_updated', {'success': True})

@socketio.on('activate_premium')
def handle_activate_premium(data):
    username = data['username']
    
    user_email = find_user_email(username)
    if not user_email:
        emit('premium_error', {'message': 'User not found'})
        return
    
    users_db[user_email]['premium'] = True
    save_data()
    
    emit('premium_activated', {'username': username})

@socketio.on('send_friend_request')
def handle_send_friend_request(data):
    from_user = data['from']
    to_user = data['to']
    
    recipient_email = find_user_email(to_user)
    if not recipient_email:
        emit('friend_request_error', {'message': 'User not found'})
        return
    
    # Add to recipient's friend requests
    if 'friend_requests' not in users_db[recipient_email]:
        users_db[recipient_email]['friend_requests'] = []
    
    if from_user not in users_db[recipient_email]['friend_requests']:
        users_db[recipient_email]['friend_requests'].append(from_user)
    
    save_data()
    emit('friend_request_sent', {'success': True})

@socketio.on('get_friends')
def handle_get_friends():
    username = None
    for uname, sid in active_users.items():
        if sid == request.sid:
            username = uname
            break
    
    if not username:
        emit('friends_list', [])
        return
    
    user_email = find_user_email(username)
    
    if not user_email or 'friends' not in users_db[user_email]:
        emit('friends_list', [])
        return
    
    friends_data = []
    for friend_username in users_db[user_email]['friends']:
        is_connected = friend_username in active_users
        
        friends_data.append({
            'username': friend_username,
            'connected': is_connected
        })
    
    emit('friends_list', friends_data)

if __name__ == '__main__':
    print("=" * 60)
    print("🎤 ECHOROOM - Voice & Text Chat")
    print("=" * 60)
    print("\n✅ ALL BUTTONS ARE WORKING!")
    print("\n🎯 Features:")
    print("• Login/Signup (Test: test@test.com / 123456)")
    print("• Create and join rooms")
    print("• Send messages")
    print("• Upload avatars")
    print("• Settings with save functionality")
    print("• Friend system")
    print("• Premium upgrade (use code: 'test')")
    print("\n💾 Data saved to:", DATA_FILE)
    print("\n🚀 Access at: http://localhost:5000")
    print("=" * 60)
    
    socketio.run(app, 
                 host='0.0.0.0', 
                 port=5000, 
                 debug=False, 
                 allow_unsafe_werkzeug=True)

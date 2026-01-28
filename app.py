#!/usr/bin/env python3
"""
Squad Talk - Full Featured Chat with Private Messages
"""

import uuid
import hashlib
import json
import os
from datetime import datetime
from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, emit, join_room

# ==================== ORIGINAL BEAUTIFUL HTML TEMPLATE ====================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚀 Squad Talk - Voice & Text Chat</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #fff;
            min-height: 100vh;
        }

        .container {
            display: flex;
            height: 100vh;
            max-width: 1600px;
            margin: 0 auto;
            box-shadow: 0 0 50px rgba(0,0,0,0.5);
        }

        /* Sidebar Styles */
        .sidebar {
            width: 280px;
            background: rgba(25, 25, 35, 0.95);
            padding: 20px;
            overflow-y: auto;
            border-right: 1px solid rgba(255,255,255,0.1);
        }

        .logo {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 30px;
            color: #00adb5;
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px;
            background: rgba(0, 173, 181, 0.1);
            border-radius: 10px;
        }

        .logo i {
            animation: pulse 2s infinite;
        }

        .nav-section {
            margin-bottom: 25px;
        }

        .nav-section h3 {
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #888;
            margin-bottom: 10px;
            padding-left: 10px;
        }

        .nav-item {
            padding: 12px 15px;
            margin: 5px 0;
            background: rgba(255,255,255,0.05);
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .nav-item:hover {
            background: rgba(0, 173, 181, 0.2);
            transform: translateX(5px);
        }

        .nav-item.active {
            background: rgba(0, 173, 181, 0.3);
            border-left: 3px solid #00adb5;
        }

        .badge {
            background: #ff2e63;
            color: white;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 11px;
            margin-left: auto;
        }

        .friends-list {
            margin-top: 10px;
        }

        .friend-item {
            padding: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
            border-radius: 6px;
            margin: 3px 0;
            cursor: pointer;
        }

        .friend-item:hover {
            background: rgba(255,255,255,0.05);
        }

        .friend-item.unread {
            background: rgba(0, 173, 181, 0.1);
            border-left: 2px solid #00adb5;
        }

        .friend-item.active-chat {
            background: rgba(0, 173, 181, 0.2);
            border-left: 3px solid #00adb5;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #43b581;
        }

        .status-dot.offline {
            background: #747f8d;
        }

        .unread-badge {
            background: #ff2e63;
            color: white;
            padding: 2px 6px;
            border-radius: 10px;
            font-size: 10px;
            margin-left: auto;
        }

        /* Main Chat Area */
        .main {
            flex: 1;
            display: flex;
            flex-direction: column;
            background: rgba(30, 30, 40, 0.95);
        }

        .chat-header {
            padding: 20px;
            background: rgba(0,0,0,0.3);
            border-bottom: 1px solid rgba(255,255,255,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
            backdrop-filter: blur(10px);
        }

        .chat-header h2 {
            display: flex;
            align-items: center;
            gap: 10px;
            color: #00adb5;
        }

        .user-info {
            display: flex;
            align-items: center;
            gap: 15px;
        }

        .premium-badge {
            background: linear-gradient(45deg, #ffd700, #ffed4e);
            color: #333;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
        }

        .chat-messages {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 15px;
            background: rgba(20, 20, 30, 0.8);
        }

        .message {
            background: rgba(255,255,255,0.07);
            padding: 15px;
            border-radius: 15px;
            max-width: 70%;
            animation: slideIn 0.3s ease;
            border: 1px solid rgba(255,255,255,0.05);
            position: relative;
        }

        .message.own {
            background: rgba(0, 173, 181, 0.2);
            align-self: flex-end;
            border-color: rgba(0, 173, 181, 0.3);
        }

        .message.private {
            background: rgba(155, 89, 182, 0.2);
            border-color: rgba(155, 89, 182, 0.3);
        }

        .message.private.own {
            background: rgba(155, 89, 182, 0.3);
        }

        .message-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            font-size: 12px;
            opacity: 0.8;
        }

        .message-content {
            line-height: 1.6;
            font-size: 15px;
        }

        .private-badge {
            background: rgba(155, 89, 182, 0.3);
            color: #9b59b6;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 10px;
            margin-left: 10px;
        }

        .emoji-picker {
            position: absolute;
            bottom: 80px;
            right: 20px;
            background: rgba(40,40,50,0.95);
            border-radius: 15px;
            padding: 15px;
            display: none;
            flex-wrap: wrap;
            gap: 10px;
            width: 300px;
            max-height: 200px;
            overflow-y: auto;
            border: 1px solid rgba(0,173,181,0.3);
            backdrop-filter: blur(10px);
            z-index: 1000;
        }

        .emoji {
            font-size: 24px;
            padding: 5px;
            cursor: pointer;
            transition: transform 0.2s;
        }

        .emoji:hover {
            transform: scale(1.3);
            background: rgba(0,173,181,0.2);
            border-radius: 5px;
        }

        .message-input-area {
            padding: 20px;
            background: rgba(0,0,0,0.3);
            border-top: 1px solid rgba(255,255,255,0.1);
            display: flex;
            gap: 10px;
            align-items: center;
            position: relative;
        }

        .message-input {
            flex: 1;
            padding: 15px 20px;
            border: none;
            border-radius: 25px;
            background: rgba(255,255,255,0.08);
            color: white;
            font-size: 16px;
            outline: none;
        }

        .message-input::placeholder {
            color: rgba(255,255,255,0.4);
        }

        .input-btn {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            border: none;
            background: #00adb5;
            color: white;
            cursor: pointer;
            font-size: 18px;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .input-btn:hover {
            background: #0099a1;
            transform: scale(1.1);
        }

        /* Voice Chat Panel */
        .voice-panel {
            width: 350px;
            background: rgba(25, 25, 35, 0.95);
            padding: 20px;
            border-left: 1px solid rgba(255,255,255,0.1);
            display: flex;
            flex-direction: column;
        }

        .voice-header {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
            color: #00adb5;
        }

        .voice-users {
            flex: 1;
            overflow-y: auto;
            margin-bottom: 20px;
        }

        .voice-user {
            padding: 15px;
            margin: 10px 0;
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
            display: flex;
            align-items: center;
            gap: 15px;
            transition: all 0.3s;
        }

        .voice-user.speaking {
            background: rgba(67,181,129,0.2);
            box-shadow: 0 0 15px rgba(67,181,129,0.3);
            border: 1px solid rgba(67,181,129,0.5);
        }

        .mic-icon {
            color: #43b581;
            font-size: 18px;
        }

        .mic-icon.muted {
            color: #ff2e63;
        }

        .voice-controls {
            margin-top: auto;
            display: flex;
            justify-content: center;
            gap: 15px;
            padding: 20px;
            background: rgba(0,0,0,0.2);
            border-radius: 15px;
        }

        .voice-btn {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            border: none;
            background: linear-gradient(135deg, #00adb5, #0099a1);
            color: white;
            cursor: pointer;
            font-size: 22px;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .voice-btn:hover {
            transform: scale(1.1);
            box-shadow: 0 0 20px rgba(0,173,181,0.5);
        }

        .voice-btn.mute {
            background: linear-gradient(135deg, #ff2e63, #d81b60);
        }

        .voice-btn.deafen {
            background: linear-gradient(135deg, #ff9a00, #ff6b00);
        }

        .voice-btn.call {
            background: linear-gradient(135deg, #43b581, #3ca374);
        }

        /* Modal Styles */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.9);
            z-index: 2000;
            justify-content: center;
            align-items: center;
            backdrop-filter: blur(5px);
        }

        .modal-content {
            background: linear-gradient(135deg, rgba(40,40,50,0.95), rgba(30,30,40,0.95));
            padding: 40px;
            border-radius: 20px;
            width: 90%;
            max-width: 500px;
            border: 1px solid rgba(0,173,181,0.3);
            box-shadow: 0 0 50px rgba(0,173,181,0.2);
        }

        .modal-header {
            margin-bottom: 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .modal-header h2 {
            color: #00adb5;
            font-size: 28px;
        }

        .close-btn {
            background: none;
            border: none;
            color: #ff2e63;
            font-size: 28px;
            cursor: pointer;
            transition: transform 0.3s;
        }

        .close-btn:hover {
            transform: rotate(90deg);
        }

        .form-group {
            margin-bottom: 25px;
        }

        .form-group label {
            display: block;
            margin-bottom: 10px;
            color: rgba(255,255,255,0.9);
            font-size: 14px;
        }

        .form-group input,
        .form-group select,
        .form-group textarea {
            width: 100%;
            padding: 15px;
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 10px;
            background: rgba(255,255,255,0.08);
            color: white;
            font-size: 16px;
            transition: all 0.3s;
        }

        .form-group input:focus,
        .form-group select:focus,
        .form-group textarea:focus {
            outline: none;
            border-color: #00adb5;
            box-shadow: 0 0 15px rgba(0,173,181,0.3);
        }

        .btn {
            padding: 15px 30px;
            background: linear-gradient(135deg, #00adb5, #0099a1);
            color: white;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            transition: all 0.3s;
            width: 100%;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(0,173,181,0.3);
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

        .btn-private {
            background: linear-gradient(135deg, #9b59b6, #8e44ad);
            color: white;
        }

        /* Premium Features */
        .premium-features {
            margin-top: 30px;
            padding: 25px;
            background: rgba(255,215,0,0.1);
            border-radius: 15px;
            border: 1px solid rgba(255,215,0,0.3);
        }

        .premium-features h3 {
            color: #ffd700;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 20px;
        }

        .feature-list {
            list-style: none;
        }

        .feature-list li {
            padding: 10px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 15px;
        }

        /* Animations */
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.1); }
            100% { transform: scale(1); }
        }

        @keyframes glow {
            0% { box-shadow: 0 0 10px rgba(0,173,181,0.5); }
            50% { box-shadow: 0 0 20px rgba(0,173,181,0.8); }
            100% { box-shadow: 0 0 10px rgba(0,173,181,0.5); }
        }

        .pulse {
            animation: pulse 2s infinite;
        }

        .glow {
            animation: glow 2s infinite;
        }

        /* Notifications */
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 25px;
            background: rgba(40,40,50,0.95);
            border-radius: 10px;
            border-left: 4px solid #00adb5;
            animation: slideIn 0.3s ease;
            z-index: 3000;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }

        .notification.success {
            border-left-color: #43b581;
        }

        .notification.error {
            border-left-color: #ff2e63;
        }

        .notification.warning {
            border-left-color: #ff9a00;
        }

        .notification.private {
            border-left-color: #9b59b6;
        }

        /* Message Options */
        .message-options {
            position: absolute;
            top: 10px;
            right: 10px;
            opacity: 0;
            transition: opacity 0.3s;
        }

        .message:hover .message-options {
            opacity: 1;
        }

        .message-options-btn {
            background: rgba(0,0,0,0.5);
            border: none;
            color: white;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            cursor: pointer;
            font-size: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .message-options-dropdown {
            position: absolute;
            top: 35px;
            right: 0;
            background: rgba(40,40,50,0.95);
            border-radius: 10px;
            padding: 10px;
            min-width: 150px;
            display: none;
            z-index: 100;
            border: 1px solid rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
        }

        .message-options-dropdown.show {
            display: block;
        }

        .message-option {
            padding: 8px 12px;
            cursor: pointer;
            border-radius: 5px;
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
        }

        .message-option:hover {
            background: rgba(255,255,255,0.1);
        }

        .message-option.delete {
            color: #ff2e63;
        }

        .message.deleted {
            opacity: 0.5;
            font-style: italic;
        }

        .message.deleted .message-content {
            color: rgba(255,255,255,0.5);
        }

        /* Responsive */
        @media (max-width: 1200px) {
            .container {
                flex-direction: column;
            }
            .sidebar, .voice-panel {
                width: 100%;
                height: auto;
            }
            .voice-panel {
                order: -1;
                border-left: none;
                border-bottom: 1px solid rgba(255,255,255,0.1);
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Left Sidebar -->
        <div class="sidebar">
            <div class="logo">
                <i class="fas fa-rocket"></i>
                Squad Talk 🚀
            </div>
            
            <div class="nav-section">
                <h3>Servers</h3>
                <div id="servers-list">
                    <!-- Servers will be populated here -->
                </div>
                <div class="nav-item" onclick="showCreateServerModal()">
                    <i class="fas fa-plus"></i>
                    <span>Create Server</span>
                </div>
            </div>

            <div class="nav-section">
                <h3>Direct Messages</h3>
                <div id="dm-list" class="friends-list">
                    <!-- Private chats will appear here -->
                </div>
                <div class="nav-item" onclick="showFriendsModal()">
                    <i class="fas fa-user-friends"></i>
                    <span>Friends</span>
                    <span id="friend-requests-badge" class="badge" style="display: none;">0</span>
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

            <div class="user-info" style="margin-top: auto; padding: 15px; background: rgba(0,0,0,0.2); border-radius: 10px;">
                <div style="flex: 1;">
                    <strong id="username-display">Guest</strong>
                    <div id="user-status" style="font-size: 12px; opacity: 0.7;">Free User</div>
                </div>
                <button class="btn" onclick="showUpgradeModal()" style="padding: 8px 16px; font-size: 12px;" id="upgrade-btn">
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
                    <div id="mic-status" style="font-size: 12px; background: #43b581; padding: 4px 12px; border-radius: 12px;">
                        <i class="fas fa-microphone"></i> Mic Ready
                    </div>
                </div>
            </div>

            <div class="chat-messages" id="chat-messages">
                <!-- Messages will appear here -->
            </div>

            <div class="message-input-area">
                <button class="input-btn" onclick="toggleEmojiPicker()">
                    <i class="far fa-smile"></i>
                </button>
                <input type="text" class="message-input" id="message-input" 
                       placeholder="Type your message here..." 
                       onkeypress="if(event.keyCode===13) sendMessage()">
                <button class="input-btn" onclick="sendMessage()">
                    <i class="fas fa-paper-plane"></i>
                </button>
                
                <div class="emoji-picker" id="emoji-picker">
                    <!-- Emojis will be populated here -->
                </div>
            </div>
        </div>

        <!-- Voice Chat Panel -->
        <div class="voice-panel">
            <div class="voice-header">
                <i class="fas fa-microphone-alt"></i> Voice Chat
                <div style="font-size: 12px; opacity: 0.7; margin-left: auto;">
                    <span id="voice-users-count">0</span> users
                </div>
            </div>
            
            <div class="voice-users" id="voice-users">
                <!-- Voice users will appear here -->
            </div>

            <div class="voice-controls">
                <button class="voice-btn" id="mute-btn" onclick="toggleMute()">
                    <i class="fas fa-microphone"></i>
                </button>
                <button class="voice-btn deafen" id="deafen-btn" onclick="toggleDeafen()">
                    <i class="fas fa-headset"></i>
                </button>
                <button class="voice-btn call" id="call-btn" onclick="startVoiceCall()">
                    <i class="fas fa-phone"></i>
                </button>
            </div>
        </div>
    </div>

    <!-- Create Server Modal -->
    <div class="modal" id="create-server-modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2><i class="fas fa-plus-circle"></i> Create New Server</h2>
                <button class="close-btn" onclick="hideCreateServerModal()">&times;</button>
            </div>
            <div class="form-group">
                <label for="server-name">Server Name</label>
                <input type="text" id="server-name" placeholder="Enter awesome server name...">
            </div>
            <div class="form-group">
                <label for="server-description">Description</label>
                <textarea id="server-description" placeholder="What's this server about?"></textarea>
            </div>
            <div class="form-group">
                <label for="server-type">Server Type</label>
                <select id="server-type">
                    <option value="public">🌐 Public (Anyone can join)</option>
                    <option value="private">🔒 Private (Invite only)</option>
                    <option value="premium">👑 Premium (Premium users only)</option>
                </select>
            </div>
            <button class="btn btn-success" onclick="createServer()">
                <i class="fas fa-rocket"></i> Launch Server
            </button>
        </div>
    </div>

    <!-- Upgrade Modal -->
    <div class="modal" id="upgrade-modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2><i class="fas fa-crown"></i> Upgrade to Premium</h2>
                <button class="close-btn" onclick="hideUpgradeModal()">&times;</button>
            </div>
            
            <div class="premium-features">
                <h3><i class="fas fa-star"></i> Premium Features</h3>
                <ul class="feature-list">
                    <li><i class="fas fa-check-circle"></i> Create unlimited servers</li>
                    <li><i class="fas fa-check-circle"></i> HD Voice & Video calls</li>
                    <li><i class="fas fa-check-circle"></i> Screen sharing & recording</li>
                    <li><i class="fas fa-check-circle"></i> Custom emojis & stickers</li>
                    <li><i class="fas fa-check-circle"></i> 500GB cloud storage</li>
                    <li><i class="fas fa-check-circle"></i> Priority 24/7 support</li>
                    <li><i class="fas fa-check-circle"></i> Video calls (100+ people)</li>
                    <li><i class="fas fa-check-circle"></i> Advanced server analytics</li>
                </ul>
            </div>

            <div style="margin-top: 30px;">
                <h3>Special Owner Code</h3>
                <div class="form-group">
                    <input type="text" id="owner-code" placeholder="Enter owner code (optional)">
                </div>
                <button class="btn btn-premium" onclick="checkOwnerCode()">
                    <i class="fas fa-key"></i> Validate Owner Code
                </button>
            </div>
        </div>
    </div>

    <!-- Login/Signup Modal -->
    <div class="modal" id="auth-modal" style="display: flex;">
        <div class="modal-content">
            <div class="modal-header">
                <h2><i class="fas fa-rocket"></i> Welcome to Squad Talk</h2>
            </div>
            
            <div id="login-section">
                <h3 style="margin-bottom: 20px; color: #00adb5;">Login</h3>
                <div class="form-group">
                    <label for="login-email">Email Address</label>
                    <input type="email" id="login-email" placeholder="your.email@gmail.com">
                </div>
                <div class="form-group">
                    <label for="login-password">Password</label>
                    <input type="password" id="login-password" placeholder="••••••••">
                </div>
                <button class="btn btn-success" onclick="login()">
                    <i class="fas fa-sign-in-alt"></i> Login
                </button>
                <div style="text-align: center; margin-top: 20px;">
                    <a href="#" onclick="showSignup()" style="color: #00adb5; text-decoration: none;">
                        Don't have an account? Sign up
                    </a>
                </div>
            </div>

            <div id="signup-section" style="display: none;">
                <h3 style="margin-bottom: 20px; color: #00adb5;">Create Account</h3>
                <div class="form-group">
                    <label for="signup-username">Username</label>
                    <input type="text" id="signup-username" placeholder="Choose a cool username">
                </div>
                <div class="form-group">
                    <label for="signup-email">Email Address</label>
                    <input type="email" id="signup-email" placeholder="your.email@gmail.com">
                </div>
                <div class="form-group">
                    <label for="signup-password">Password</label>
                    <input type="password" id="signup-password" placeholder="••••••••">
                </div>
                <button class="btn btn-success" onclick="signup()">
                    <i class="fas fa-user-plus"></i> Create Account
                </button>
                <div style="text-align: center; margin-top: 20px;">
                    <a href="#" onclick="showLogin()" style="color: #00adb5; text-decoration: none;">
                        Already have an account? Login
                    </a>
                </div>
            </div>
        </div>
    </div>

    <!-- Friends Modal -->
    <div class="modal" id="friends-modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2><i class="fas fa-user-friends"></i> Friends</h2>
                <button class="close-btn" onclick="hideFriendsModal()">&times;</button>
            </div>
            <div id="friend-requests-section">
                <h3>Friend Requests</h3>
                <div id="friend-requests-list">
                    <!-- Friend requests will appear here -->
                </div>
            </div>
            <div style="margin-top: 30px;">
                <h3>Online Friends</h3>
                <div id="online-friends-list">
                    <!-- Online friends will appear here -->
                </div>
            </div>
            <div style="margin-top: 30px;">
                <h3>All Friends</h3>
                <div id="all-friends-list">
                    <!-- All friends will appear here -->
                </div>
            </div>
        </div>
    </div>

    <!-- Add Friend Modal -->
    <div class="modal" id="add-friend-modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2><i class="fas fa-user-plus"></i> Add Friend</h2>
                <button class="close-btn" onclick="hideAddFriendModal()">&times;</button>
            </div>
            <div class="form-group">
                <label for="friend-username">Username or Email</label>
                <input type="text" id="friend-username" placeholder="Enter username or email">
            </div>
            <button class="btn btn-success" onclick="sendFriendRequest()">
                <i class="fas fa-paper-plane"></i> Send Friend Request
            </button>
        </div>
    </div>

    <!-- Notification Container -->
    <div id="notification-container"></div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.0/socket.io.min.js"></script>
    <script>
        // Global variables
        let socket;
        let currentUser = '';
        let currentChat = { type: 'server', id: 'general', name: 'General' };
        let isMuted = false;
        let isDeafened = false;
        let selectedPlan = '';
        let localStream = null;
        let peerConnections = {};
        let emojis = ['😀', '😂', '🤣', '😍', '😎', '😭', '😡', '🥰', '😘', '🤔', '👋', '👍', '👏', '🎉', '🔥', '⭐', '🌟', '💯', '❤️', '💙', '💚', '💛', '💜', '🤑', '🤯', '🥳', '😱', '🤩', '😴', '💀', '👻', '🤖', '👾', '🐱', '🐶', '🦊', '🐯', '🦁', '🐮', '🐷', '🐸', '🐵'];
        let unreadCounts = {};
        
        // Emoji categories
        const emojiCategories = {
            'Smileys': ['😀', '😂', '🤣', '😍', '😎', '😭', '😡', '🥰', '😘', '🤔', '😴', '😱'],
            'Gestures': ['👋', '👍', '👏', '🙏', '🤝', '✌️', '🤘', '👌'],
            'Objects': ['🎉', '🔥', '⭐', '🌟', '💯', '🎁', '🎈', '🎊'],
            'Hearts': ['❤️', '💙', '💚', '💛', '💜', '🖤', '🤍', '💔'],
            'Animals': ['🐱', '🐶', '🦊', '🐯', '🦁', '🐮', '🐷', '🐸', '🐵'],
            'Food': ['🍕', '🍔', '🍟', '🍦', '🍩', '🍎', '🍌', '🍇'],
            'Symbols': ['✅', '❌', '⚠️', '⛔', '♻️', '⚡', '❓', '❗']
        };

        // Initialize WebSocket connection
        function initWebSocket() {
            socket = io();
            
            socket.on('connect', () => {
                console.log('Connected to server');
                updateConnectionStatus(true);
                showNotification('Connected to Squad Talk!', 'success');
                
                // If user was logged in, restore session
                const savedUser = localStorage.getItem('squadTalkUser');
                if (savedUser) {
                    const userData = JSON.parse(savedUser);
                    socket.emit('restore_session', userData);
                }
            });

            socket.on('disconnect', () => {
                console.log('Disconnected from server');
                updateConnectionStatus(false);
                showNotification('Disconnected from server', 'error');
            });

            socket.on('message', (data) => {
                if (data.type === 'private') {
                    handlePrivateMessage(data);
                } else {
                    // Server message
                    if (currentChat.type === 'server' && currentChat.id === data.server) {
                        addMessage(data);
                    }
                }
            });

            socket.on('private_message', (data) => {
                handlePrivateMessage(data);
            });

            socket.on('user_joined', (data) => {
                if (currentChat.type === 'server' && currentChat.id === data.server) {
                    addSystemMessage(`${data.username} joined the chat`, 'join');
                    updateVoiceUsers(data.users);
                    updateVoiceUserCount(data.users.length);
                }
            });

            socket.on('user_left', (data) => {
                if (currentChat.type === 'server' && currentChat.id === data.server) {
                    addSystemMessage(`${data.username} left the chat`, 'leave');
                    updateVoiceUsers(data.users);
                    updateVoiceUserCount(data.users.length);
                }
            });

            socket.on('server_created', (data) => {
                addServerToList(data.server);
                showNotification(`Server "${data.server.name}" created!`, 'success');
            });

            socket.on('update_voice_users', (data) => {
                updateVoiceUsers(data.users);
                updateVoiceUserCount(data.users.length);
            });

            socket.on('friend_request', (data) => {
                showNotification(`Friend request from ${data.from}`, 'warning');
                updateFriendRequestsBadge();
                socket.emit('get_friend_requests');
            });

            socket.on('friend_request_accepted', (data) => {
                showNotification(`${data.username} accepted your friend request!`, 'success');
                socket.emit('get_friends');
                loadPrivateChats();
            });

            socket.on('friend_request_rejected', (data) => {
                showNotification(`${data.username} rejected your friend request`, 'error');
            });

            socket.on('user_upgraded', (data) => {
                if (data.username === currentUser) {
                    showNotification('You are now a Premium user! 🎉', 'success');
                    updateUserPremiumStatus(true);
                    localStorage.setItem('squadTalkUser', JSON.stringify({
                        username: currentUser,
                        premium: true
                    }));
                }
            });

            socket.on('session_restored', (data) => {
                currentUser = data.username;
                document.getElementById('username-display').textContent = data.username;
                document.getElementById('auth-modal').style.display = 'none';
                
                if (data.premium) {
                    updateUserPremiumStatus(true);
                }
                
                socket.emit('join', {
                    username: data.username,
                    server: 'general'
                });
                
                showNotification(`Welcome back, ${data.username}! 🎉`, 'success');
                
                // Load data
                socket.emit('get_servers');
                socket.emit('get_friends');
                socket.emit('get_friend_requests');
                loadPrivateChats();
            });

            // Load existing servers
            socket.on('server_list', (servers) => {
                servers.forEach(server => addServerToList(server));
            });

            // Load friend requests
            socket.on('friend_requests_list', (requests) => {
                updateFriendRequestsList(requests);
                updateFriendRequestsBadge(requests.length);
            });

            // Load friends
            socket.on('friends_list', (friends) => {
                updateFriendsList(friends);
            });

            // Load messages for chat
            socket.on('chat_messages', (messages) => {
                const messagesDiv = document.getElementById('chat-messages');
                messagesDiv.innerHTML = '';
                
                if (messages && messages.length > 0) {
                    messages.forEach(msg => {
                        addMessage(msg);
                    });
                } else {
                    if (currentChat.type === 'server') {
                        addSystemMessage('Welcome to the server! Start chatting now.', 'info');
                    } else {
                        addSystemMessage(`Start a private conversation with ${currentChat.name}!`, 'info');
                    }
                }
                
                // Mark chat as read
                markChatAsRead(currentChat);
            });

            socket.on('private_chats_list', (chats) => {
                updatePrivateChatsList(chats);
            });
        }

        // UI Functions
        function showCreateServerModal() {
            document.getElementById('create-server-modal').style.display = 'flex';
        }

        function hideCreateServerModal() {
            document.getElementById('create-server-modal').style.display = 'none';
        }

        function showUpgradeModal() {
            document.getElementById('upgrade-modal').style.display = 'flex';
        }

        function hideUpgradeModal() {
            document.getElementById('upgrade-modal').style.display = 'none';
        }

        function showFriendsModal() {
            socket.emit('get_friend_requests');
            socket.emit('get_friends');
            document.getElementById('friends-modal').style.display = 'flex';
        }

        function hideFriendsModal() {
            document.getElementById('friends-modal').style.display = 'none';
        }

        function showAddFriendModal() {
            document.getElementById('add-friend-modal').style.display = 'flex';
        }

        function hideAddFriendModal() {
            document.getElementById('add-friend-modal').style.display = 'none';
        }

        function showSignup() {
            document.getElementById('login-section').style.display = 'none';
            document.getElementById('signup-section').style.display = 'block';
        }

        function showLogin() {
            document.getElementById('signup-section').style.display = 'none';
            document.getElementById('login-section').style.display = 'block';
        }

        function showNotification(message, type = 'info') {
            const container = document.getElementById('notification-container');
            const notification = document.createElement('div');
            notification.className = `notification ${type}`;
            notification.innerHTML = `
                <div style="display: flex; align-items: center; gap: 10px;">
                    <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'times-circle' : type === 'warning' ? 'exclamation-circle' : type === 'private' ? 'user-friends' : 'info-circle'}"></i>
                    <span>${message}</span>
                </div>
            `;
            
            container.appendChild(notification);
            
            setTimeout(() => {
                notification.style.opacity = '0';
                notification.style.transform = 'translateX(100px)';
                setTimeout(() => notification.remove(), 300);
            }, 3000);
        }

        // Authentication Functions
        function login() {
            const email = document.getElementById('login-email').value.trim();
            const password = document.getElementById('login-password').value.trim();
            
            if (!email || !password) {
                showNotification('Please fill all fields', 'error');
                return;
            }
            
            socket.emit('login', {
                email: email,
                password: password
            });
            
            socket.on('login_success', (data) => {
                currentUser = data.username;
                document.getElementById('username-display').textContent = data.username;
                document.getElementById('auth-modal').style.display = 'none';
                
                // Save user session
                localStorage.setItem('squadTalkUser', JSON.stringify({
                    username: data.username,
                    premium: data.premium
                }));
                
                if (data.premium) {
                    updateUserPremiumStatus(true);
                }
                
                socket.emit('join', {
                    username: data.username,
                    server: 'general'
                });
                
                // Load data
                socket.emit('get_servers');
                socket.emit('get_friends');
                socket.emit('get_friend_requests');
                loadPrivateChats();
                
                showNotification(`Welcome back, ${data.username}! 🎉`, 'success');
            });
            
            socket.on('login_error', (data) => {
                showNotification(data.message, 'error');
            });
        }

        function signup() {
            const username = document.getElementById('signup-username').value.trim();
            const email = document.getElementById('signup-email').value.trim();
            const password = document.getElementById('signup-password').value.trim();
            
            if (!username || !email || !password) {
                showNotification('Please fill all fields', 'error');
                return;
            }
            
            if (password.length < 6) {
                showNotification('Password must be at least 6 characters', 'error');
                return;
            }
            
            socket.emit('signup', {
                username: username,
                email: email,
                password: password
            });
            
            socket.on('signup_success', (data) => {
                showNotification('Account created successfully! Please login.', 'success');
                showLogin();
            });
            
            socket.on('signup_error', (data) => {
                showNotification(data.message, 'error');
            });
        }

        // Server Functions
        function createServer() {
            const name = document.getElementById('server-name').value.trim();
            const description = document.getElementById('server-description').value.trim();
            const type = document.getElementById('server-type').value;
            
            if (!name) {
                showNotification('Please enter a server name', 'error');
                return;
            }
            
            socket.emit('create_server', {
                name: name,
                description: description,
                type: type,
                creator: currentUser
            });
            
            hideCreateServerModal();
        }

        function joinServer(serverId, serverName) {
            currentChat = { type: 'server', id: serverId, name: serverName };
            document.getElementById('current-chat-name').innerHTML = 
                `<i class="fas fa-hashtag"></i> ${serverName}`;
            
            // Clear current messages
            document.getElementById('chat-messages').innerHTML = '';
            
            // Join server room
            socket.emit('join_server', { 
                server: serverId, 
                username: currentUser 
            });
            
            // Request messages for this server
            socket.emit('get_server_messages', { server: serverId });
            
            addSystemMessage(`Joined ${serverName}`, 'join');
            
            // Update active state
            updateActiveChat();
            markChatAsRead(currentChat);
        }

        // Private Chat Functions
        function startPrivateChat(friendUsername) {
            const chatId = getPrivateChatId(currentUser, friendUsername);
            currentChat = { type: 'private', id: chatId, name: friendUsername, with: friendUsername };
            document.getElementById('current-chat-name').innerHTML = 
                `<i class="fas fa-user-friends"></i> ${friendUsername}`;
            
            // Clear current messages
            document.getElementById('chat-messages').innerHTML = '';
            
            // Request messages for this private chat
            socket.emit('get_private_messages', { 
                user1: currentUser, 
                user2: friendUsername 
            });
            
            addSystemMessage(`Started private chat with ${friendUsername}`, 'private');
            
            // Update active state
            updateActiveChat();
            markChatAsRead(currentChat);
        }

        function handlePrivateMessage(data) {
            const chatId = getPrivateChatId(data.sender, data.receiver);
            
            // Add to chat list if not already there
            if (!document.querySelector(`[data-chat-id="${chatId}"]`)) {
                addPrivateChatToList({ 
                    id: chatId, 
                    username: data.sender === currentUser ? data.receiver : data.sender,
                    unread: 0 
                });
            }
            
            // If this chat is currently open, show message
            if (currentChat.type === 'private' && currentChat.id === chatId) {
                addMessage({
                    ...data,
                    username: data.sender,
                    message: data.message,
                    isPrivate: true
                });
                markChatAsRead(currentChat);
            } else {
                // Otherwise, increment unread count
                incrementUnreadCount(chatId);
                showNotification(`New message from ${data.sender}`, 'private');
            }
        }

        function getPrivateChatId(user1, user2) {
            return [user1, user2].sort().join('_');
        }

        function loadPrivateChats() {
            socket.emit('get_private_chats', { username: currentUser });
        }

        function updatePrivateChatsList(chats) {
            const dmList = document.getElementById('dm-list');
            dmList.innerHTML = '';
            
            if (chats.length === 0) {
                dmList.innerHTML = '<div style="opacity: 0.7; text-align: center; padding: 10px;">No private chats</div>';
                return;
            }
            
            chats.forEach(chat => {
                addPrivateChatToList(chat);
            });
        }

        function addPrivateChatToList(chat) {
            const dmList = document.getElementById('dm-list');
            
            // Check if chat already exists
            if (document.querySelector(`[data-chat-id="${chat.id}"]`)) {
                return;
            }
            
            const chatDiv = document.createElement('div');
            chatDiv.className = `friend-item ${currentChat.type === 'private' && currentChat.id === chat.id ? 'active-chat' : ''} ${chat.unread > 0 ? 'unread' : ''}`;
            chatDiv.setAttribute('data-chat-id', chat.id);
            chatDiv.innerHTML = `
                <i class="fas fa-user-circle"></i>
                <span>${chat.username}</span>
                ${chat.unread > 0 ? `<span class="unread-badge">${chat.unread}</span>` : ''}
            `;
            
            chatDiv.onclick = () => {
                startPrivateChat(chat.username);
            };
            
            dmList.appendChild(chatDiv);
        }

        function markChatAsRead(chat) {
            if (!chat) return;
            
            const chatId = chat.type === 'private' ? chat.id : chat.id;
            const chatElement = document.querySelector(`[data-chat-id="${chatId}"]`);
            
            if (chatElement) {
                chatElement.classList.remove('unread');
                const badge = chatElement.querySelector('.unread-badge');
                if (badge) {
                    badge.remove();
                }
            }
            
            if (chat.type === 'private') {
                socket.emit('mark_chat_read', { 
                    chatId: chatId,
                    username: currentUser 
                });
            }
        }

        function incrementUnreadCount(chatId) {
            const chatElement = document.querySelector(`[data-chat-id="${chatId}"]`);
            
            if (chatElement) {
                let badge = chatElement.querySelector('.unread-badge');
                
                if (!badge) {
                    badge = document.createElement('span');
                    badge.className = 'unread-badge';
                    chatElement.appendChild(badge);
                }
                
                const currentCount = parseInt(badge.textContent) || 0;
                badge.textContent = currentCount + 1;
                chatElement.classList.add('unread');
            }
        }

        function updateActiveChat() {
            // Update server list
            document.querySelectorAll('#servers-list .nav-item').forEach(item => {
                item.classList.remove('active');
                if (currentChat.type === 'server' && item.getAttribute('data-server-id') === currentChat.id) {
                    item.classList.add('active');
                }
            });
            
            // Update DM list
            document.querySelectorAll('#dm-list .friend-item').forEach(item => {
                item.classList.remove('active-chat');
                if (currentChat.type === 'private' && item.getAttribute('data-chat-id') === currentChat.id) {
                    item.classList.add('active-chat');
                }
            });
            
            // Update friends list
            document.querySelectorAll('#friends-list .friend-item').forEach(item => {
                item.classList.remove('active-chat');
                if (currentChat.type === 'private' && item.textContent.includes(currentChat.name)) {
                    item.classList.add('active-chat');
                }
            });
        }

        // Premium Functions
        function checkOwnerCode() {
            const code = document.getElementById('owner-code').value.trim();
            
            if (code === "i'm the owner") {
                socket.emit('upgrade_user', { 
                    username: currentUser, 
                    plan: 'owner',
                    code: code 
                });
                showNotification('🎉 Owner code accepted! Welcome, owner!', 'success');
                hideUpgradeModal();
            } else {
                showNotification('Invalid owner code', 'error');
            }
        }

        // Friend Functions
        function sendFriendRequest() {
            const friendInput = document.getElementById('friend-username').value.trim();
            
            if (!friendInput) {
                showNotification('Please enter username or email', 'error');
                return;
            }
            
            socket.emit('send_friend_request', {
                from: currentUser,
                to: friendInput
            });
            
            socket.on('friend_request_sent', (data) => {
                showNotification(`Friend request sent to ${friendInput}`, 'success');
                hideAddFriendModal();
            });
            
            socket.on('friend_request_error', (data) => {
                showNotification(data.message, 'error');
            });
        }

        function acceptFriendRequest(from) {
            socket.emit('accept_friend_request', {
                from: from,
                to: currentUser
            });
        }

        function rejectFriendRequest(from) {
            socket.emit('reject_friend_request', {
                from: from,
                to: currentUser
            });
        }

        function updateFriendRequestsList(requests) {
            const list = document.getElementById('friend-requests-list');
            list.innerHTML = '';
            
            if (requests.length === 0) {
                list.innerHTML = '<div style="opacity: 0.7; text-align: center; padding: 20px;">No friend requests</div>';
                return;
            }
            
            requests.forEach(request => {
                const requestDiv = document.createElement('div');
                requestDiv.className = 'friend-item';
                requestDiv.innerHTML = `
                    <i class="fas fa-user-circle"></i>
                    <span>${request.from}</span>
                    <div style="flex: 1;"></div>
                    <button class="btn" style="padding: 5px 10px; font-size: 12px;" onclick="acceptFriendRequest('${request.from}')">
                        <i class="fas fa-check"></i> Accept
                    </button>
                    <button class="btn btn-danger" style="padding: 5px 10px; font-size: 12px; margin-left: 5px;" onclick="rejectFriendRequest('${request.from}')">
                        <i class="fas fa-times"></i> Reject
                    </button>
                `;
                list.appendChild(requestDiv);
            });
        }

        function updateFriendsList(friends) {
            const friendsList = document.getElementById('friends-list');
            const onlineList = document.getElementById('online-friends-list');
            const allList = document.getElementById('all-friends-list');
            
            friendsList.innerHTML = '';
            onlineList.innerHTML = '';
            allList.innerHTML = '';
            
            let onlineCount = 0;
            
            friends.forEach(friend => {
                const friendDiv = document.createElement('div');
                friendDiv.className = `friend-item ${currentChat.type === 'private' && currentChat.with === friend.username ? 'active-chat' : ''}`;
                friendDiv.innerHTML = `
                    <div class="status-dot ${friend.connected ? '' : 'offline'}"></div>
                    <i class="fas fa-user-circle"></i>
                    <span>${friend.username}</span>
                    ${friend.premium ? '<i class="fas fa-crown" style="color: #ffd700;"></i>' : ''}
                    <div style="flex: 1;"></div>
                    <button class="btn btn-private" style="padding: 3px 8px; font-size: 11px;" onclick="startPrivateChat('${friend.username}')">
                        <i class="fas fa-comment"></i> Chat
                    </button>
                `;
                
                friendsList.appendChild(friendDiv);
                
                const friendDivCopy = friendDiv.cloneNode(true);
                if (friend.connected) {
                    onlineCount++;
                    onlineList.appendChild(friendDivCopy);
                }
                allList.appendChild(friendDivCopy);
            });
            
            if (onlineCount === 0) {
                onlineList.innerHTML = '<div style="opacity: 0.7; text-align: center; padding: 20px;">No friends online</div>';
            }
            
            if (friends.length === 0) {
                friendsList.innerHTML = '<div style="opacity: 0.7; text-align: center; padding: 10px;">No friends yet</div>';
                allList.innerHTML = '<div style="opacity: 0.7; text-align: center; padding: 20px;">No friends yet</div>';
            }
        }

        function updateFriendRequestsBadge(count) {
            const badge = document.getElementById('friend-requests-badge');
            if (count > 0) {
                badge.style.display = 'inline-block';
                badge.textContent = count;
            } else {
                badge.style.display = 'none';
            }
        }

        // Chat Functions
        function sendMessage() {
            const input = document.getElementById('message-input');
            const message = input.value.trim();
            
            if (!message || !currentUser) {
                showNotification('Please login first', 'error');
                return;
            }
            
            if (currentChat.type === 'server') {
                socket.emit('message', {
                    username: currentUser,
                    message: message,
                    server: currentChat.id,
                    timestamp: new Date().toISOString()
                });
            } else if (currentChat.type === 'private') {
                socket.emit('private_message', {
                    sender: currentUser,
                    receiver: currentChat.with,
                    message: message,
                    timestamp: new Date().toISOString()
                });
            }
            
            input.value = '';
            input.focus();
            hideEmojiPicker();
        }

        function addMessage(data) {
            const messagesDiv = document.getElementById('chat-messages');
            
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${data.username === currentUser ? 'own' : ''} ${data.isPrivate ? 'private' : ''}`;
            
            // Parse emojis in message
            let messageContent = data.message;
            messageContent = messageContent.replace(/:[a-z_]+:/g, match => {
                const emojiName = match.slice(1, -1);
                return emojis.find(e => e.includes(emojiName)) || match;
            });
            
            messageDiv.innerHTML = `
                <div class="message-header">
                    <strong>${data.username}</strong>
                    <span>${new Date(data.timestamp).toLocaleTimeString()}</span>
                    ${data.isPrivate ? '<span class="private-badge">Private</span>' : ''}
                </div>
                <div class="message-content">${messageContent}</div>
            `;
            
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        function addSystemMessage(text, type = 'info') {
            const messagesDiv = document.getElementById('chat-messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message';
            messageDiv.style.opacity = '0.7';
            messageDiv.style.fontStyle = 'italic';
            messageDiv.style.color = type === 'join' ? '#43b581' : 
                                   type === 'leave' ? '#ff2e63' : 
                                   type === 'private' ? '#9b59b6' : '#00adb5';
            messageDiv.textContent = text;
            
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        function toggleEmojiPicker() {
            const picker = document.getElementById('emoji-picker');
            if (picker.style.display === 'flex') {
                hideEmojiPicker();
            } else {
                showEmojiPicker();
            }
        }

        function showEmojiPicker() {
            const picker = document.getElementById('emoji-picker');
            picker.innerHTML = '';
            
            Object.keys(emojiCategories).forEach(category => {
                const categoryDiv = document.createElement('div');
                categoryDiv.style.width = '100%';
                categoryDiv.style.marginBottom = '10px';
                categoryDiv.innerHTML = `<div style="font-size: 12px; opacity: 0.7; margin-bottom: 5px;">${category}</div>`;
                
                emojiCategories[category].forEach(emoji => {
                    const emojiSpan = document.createElement('span');
                    emojiSpan.className = 'emoji';
                    emojiSpan.textContent = emoji;
                    emojiSpan.onclick = () => insertEmoji(emoji);
                    categoryDiv.appendChild(emojiSpan);
                });
                
                picker.appendChild(categoryDiv);
            });
            
            picker.style.display = 'flex';
        }

        function hideEmojiPicker() {
            document.getElementById('emoji-picker').style.display = 'none';
        }

        function insertEmoji(emoji) {
            const input = document.getElementById('message-input');
            input.value += emoji;
            input.focus();
        }

        function addServerToList(server) {
            const serversList = document.getElementById('servers-list');
            
            const existing = Array.from(serversList.children).find(child => 
                child.getAttribute('data-server-id') === server.id
            );
            
            if (existing) return;
            
            const serverDiv = document.createElement('div');
            serverDiv.className = 'nav-item';
            serverDiv.setAttribute('data-server-id', server.id);
            serverDiv.innerHTML = `
                <i class="fas fa-server"></i>
                <span>${server.name}</span>
                ${server.type === 'premium' ? '<i class="fas fa-crown" style="color: #ffd700;"></i>' : ''}
            `;
            
            serverDiv.onclick = () => {
                joinServer(server.id, server.name);
            };
            
            serversList.appendChild(serverDiv);
        }

        function updateVoiceUsers(users) {
            const voiceUsersDiv = document.getElementById('voice-users');
            voiceUsersDiv.innerHTML = '';
            
            if (!users || users.length === 0) {
                voiceUsersDiv.innerHTML = '<div style="opacity: 0.7; text-align: center; padding: 20px;">No users in voice chat</div>';
                return;
            }
            
            users.forEach(user => {
                const userDiv = document.createElement('div');
                userDiv.className = `voice-user ${user.speaking ? 'speaking' : ''}`;
                userDiv.innerHTML = `
                    <i class="fas fa-user-circle"></i>
                    <div>
                        <div style="font-weight: bold;">${user.username}</div>
                        <div style="font-size: 12px; opacity: 0.7;">${user.connected ? 'Online' : 'Offline'}</div>
                    </div>
                    <div style="flex: 1;"></div>
                    <i class="fas fa-microphone ${user.muted ? 'muted mic-icon' : 'mic-icon'}"></i>
                    ${user.premium ? '<i class="fas fa-crown" style="color: #ffd700; margin-left: 10px;"></i>' : ''}
                `;
                voiceUsersDiv.appendChild(userDiv);
            });
        }

        function updateVoiceUserCount(count) {
            document.getElementById('voice-users-count').textContent = count;
        }

        // Voice Functions
        async function toggleMute() {
            isMuted = !isMuted;
            const btn = document.getElementById('mute-btn');
            btn.innerHTML = isMuted ? '<i class="fas fa-microphone-slash"></i>' : '<i class="fas fa-microphone"></i>';
            btn.className = `voice-btn ${isMuted ? 'mute' : ''}`;
            
            if (localStream) {
                localStream.getAudioTracks()[0].enabled = !isMuted;
                document.getElementById('mic-status').innerHTML = 
                    isMuted ? '<i class="fas fa-microphone-slash"></i> Mic Muted' : '<i class="fas fa-microphone"></i> Mic Active';
                document.getElementById('mic-status').style.background = isMuted ? '#ff2e63' : '#43b581';
            }
            
            socket.emit('voice_status', { muted: isMuted, username: currentUser });
        }

        function toggleDeafen() {
            isDeafened = !isDeafened;
            const btn = document.getElementById('deafen-btn');
            btn.innerHTML = isDeafened ? '<i class="fas fa-deaf"></i>' : '<i class="fas fa-headset"></i>';
        }

        async function startVoiceCall() {
            try {
                if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                    showNotification('Microphone access not supported in this browser', 'error');
                    return;
                }
                
                localStream = await navigator.mediaDevices.getUserMedia({ 
                    audio: true,
                    video: false
                });
                
                document.getElementById('mic-status').innerHTML = '<i class="fas fa-microphone"></i> Mic Active';
                document.getElementById('mic-status').classList.add('glow');
                
                socket.emit('start_voice', { username: currentUser });
                document.getElementById('call-btn').classList.add('pulse');
                
                showNotification('Voice chat started! 🎤', 'success');
                
            } catch (error) {
                console.error('Error accessing microphone:', error);
                showNotification('Could not access microphone', 'error');
            }
        }

        function updateConnectionStatus(connected) {
            const status = document.getElementById('connection-status');
            if (connected) {
                status.innerHTML = '<i class="fas fa-wifi"></i> Connected';
                status.style.background = 'linear-gradient(45deg, #43b581, #3ca374)';
            } else {
                status.innerHTML = '<i class="fas fa-wifi-slash"></i> Disconnected';
                status.style.background = 'linear-gradient(45deg, #ff2e63, #d81b60)';
            }
        }

        function updateUserPremiumStatus(isPremium) {
            document.getElementById('user-status').textContent = isPremium ? '👑 Premium User' : 'Free User';
            document.getElementById('user-status').style.color = isPremium ? '#ffd700' : '';
            
            const upgradeBtn = document.getElementById('upgrade-btn');
            if (isPremium) {
                upgradeBtn.style.display = 'none';
                localStorage.setItem('squadTalkPremium', 'true');
            } else {
                upgradeBtn.style.display = 'block';
                localStorage.removeItem('squadTalkPremium');
            }
            
            if (isPremium) {
                const badge = document.createElement('div');
                badge.className = 'premium-badge';
                badge.innerHTML = '<i class="fas fa-crown"></i> Premium';
                document.querySelector('.user-info').appendChild(badge);
            }
        }

        // Initialize when page loads
        window.onload = function() {
            initWebSocket();
            
            document.getElementById('login-email').focus();
            
            document.getElementById('login-email').onkeypress = function(e) {
                if (e.keyCode === 13) login();
            };
            document.getElementById('login-password').onkeypress = function(e) {
                if (e.keyCode === 13) login();
            };
            
            document.getElementById('message-input').onkeypress = function(e) {
                if (e.keyCode === 13) sendMessage();
            };
            
            document.addEventListener('click', function(event) {
                const picker = document.getElementById('emoji-picker');
                if (picker.style.display === 'flex' && !picker.contains(event.target) && 
                    !event.target.closest('.input-btn')) {
                    hideEmojiPicker();
                }
            });
            
            const savedPremium = localStorage.getItem('squadTalkPremium');
            if (savedPremium === 'true') {
                updateUserPremiumStatus(true);
            }
        };
    </script>
</body>
</html>
"""

# ==================== BACKEND CODE ====================

app = Flask(__name__)
app.secret_key = 'squad-talk-secret-key-2025'
socketio = SocketIO(app, 
                   cors_allowed_origins="*",
                   async_mode='threading')  # Fixed for Python 3.14

DATA_FILE = 'squad_talk_data.json'

def load_data():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {
        'users_db': {},
        'servers_db': {},
        'messages_db': {},
        'private_messages': {},
        'friend_requests': {}
    }

def save_data():
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump({
                'users_db': users_db,
                'servers_db': servers_db,
                'messages_db': messages_db,
                'private_messages': private_messages,
                'friend_requests': friend_requests_db
            }, f, indent=2)
    except Exception as e:
        print(f"Error saving data: {e}")

# Load data
data = load_data()
users_db = data.get('users_db', {})
servers_db = data.get('servers_db', {})
messages_db = data.get('messages_db', {})
private_messages = data.get('private_messages', {})
friend_requests_db = data.get('friend_requests', {})

active_users = {}

if "general" not in servers_db:
    servers_db["general"] = {
        'id': 'general',
        'name': 'General',
        'description': 'Welcome to Squad Talk!',
        'type': 'public',
        'creator': 'system',
        'created_at': datetime.now().isoformat(),
        'members': []
    }
    save_data()

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

# Helper functions
def find_user_email(username):
    for email, user_data in users_db.items():
        if user_data['username'] == username:
            return email
    return None

def get_private_chat_id(user1, user2):
    return '_'.join(sorted([user1, user2]))

# SocketIO Events
@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    for username, user_data in list(active_users.items()):
        if user_data['sid'] == request.sid:
            del active_users[username]
            break

@socketio.on('restore_session')
def handle_restore_session(data):
    username = data.get('username')
    
    user_email = find_user_email(username)
    if not user_email:
        emit('session_error', {'message': 'Session expired'})
        return
    
    user_data = users_db[user_email]
    active_users[username] = {
        'user': {'username': username, 'email': user_email},
        'sid': request.sid
    }
    
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
        'friend_requests': [],
        'private_chats': []
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
    active_users[username] = {
        'user': {'username': username, 'email': email},
        'sid': request.sid
    }
    
    emit('login_success', {
        'username': username,
        'premium': user_data.get('premium', False)
    })

@socketio.on('join')
def handle_join(data):
    username = data['username']
    server = data.get('server', 'general')
    
    if username in active_users:
        join_room(server)
        
        # Send existing messages
        server_messages = messages_db.get(server, [])
        for msg in server_messages[-50:]:
            emit('message', msg, room=request.sid)

@socketio.on('join_server')
def handle_join_server(data):
    username = data['username']
    server_id = data['server']
    
    if username in active_users:
        join_room(server_id)

@socketio.on('message')
def handle_message(data):
    message_id = str(uuid.uuid4())[:8]
    message = {
        'id': message_id,
        'username': data['username'],
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

@socketio.on('private_message')
def handle_private_message(data):
    message_id = str(uuid.uuid4())[:8]
    chat_id = get_private_chat_id(data['sender'], data['receiver'])
    
    message = {
        'id': message_id,
        'sender': data['sender'],
        'receiver': data['receiver'],
        'message': data['message'],
        'timestamp': data.get('timestamp', datetime.now().isoformat()),
        'chat_id': chat_id,
        'type': 'private'
    }
    
    if chat_id not in private_messages:
        private_messages[chat_id] = []
    private_messages[chat_id].append(message)
    
    if len(private_messages[chat_id]) > 1000:
        private_messages[chat_id] = private_messages[chat_id][-1000:]
    
    # Save data
    save_data()
    
    # Update users' chat lists
    for user in [data['sender'], data['receiver']]:
        user_email = find_user_email(user)
        if user_email and user in users_db:
            if 'private_chats' not in users_db[user_email]:
                users_db[user_email]['private_chats'] = []
            
            other_user = data['receiver'] if user == data['sender'] else data['sender']
            chat_info = {'chat_id': chat_id, 'with': other_user}
            
            if chat_info not in users_db[user_email]['private_chats']:
                users_db[user_email]['private_chats'].append(chat_info)
    
    save_data()
    
    # Send to both users if they're online
    for user in [data['sender'], data['receiver']]:
        if user in active_users:
            emit('private_message', message, room=active_users[user]['sid'])

@socketio.on('get_server_messages')
def handle_get_server_messages(data):
    server_id = data['server']
    server_messages = messages_db.get(server_id, [])
    emit('chat_messages', server_messages[-100:])

@socketio.on('get_private_messages')
def handle_get_private_messages(data):
    chat_id = get_private_chat_id(data['user1'], data['user2'])
    messages = private_messages.get(chat_id, [])
    emit('chat_messages', messages[-100:])

@socketio.on('get_private_chats')
def handle_get_private_chats(data):
    username = data['username']
    user_email = find_user_email(username)
    
    if not user_email or 'private_chats' not in users_db[user_email]:
        emit('private_chats_list', [])
        return
    
    chats = []
    for chat_info in users_db[user_email]['private_chats']:
        other_user = chat_info['with']
        chat_id = chat_info['chat_id']
        
        # Get unread count (simplified - you can enhance this)
        unread = 0
        
        chats.append({
            'id': chat_id,
            'username': other_user,
            'unread': unread
        })
    
    emit('private_chats_list', chats)

@socketio.on('mark_chat_read')
def handle_mark_chat_read(data):
    # Implement marking chat as read (update unread counts)
    pass

@socketio.on('create_server')
def handle_create_server(data):
    server_id = str(uuid.uuid4())[:8]
    server = {
        'id': server_id,
        'name': data['name'],
        'description': data.get('description', ''),
        'type': data.get('type', 'public'),
        'creator': data['creator'],
        'created_at': datetime.now().isoformat(),
        'members': [data['creator']]
    }
    
    servers_db[server_id] = server
    save_data()
    
    if data['creator'] in active_users:
        join_room(server_id)
    
    emit('server_created', {'server': server})
    emit('server_list', list(servers_db.values()), broadcast=True)

@socketio.on('get_servers')
def handle_get_servers():
    emit('server_list', list(servers_db.values()))

@socketio.on('upgrade_user')
def handle_upgrade_user(data):
    username = data['username']
    code = data.get('code', '')
    
    if username not in active_users:
        return
    
    user_email = find_user_email(username)
    if not user_email:
        return
    
    if code == "i'm the owner":
        users_db[user_email]['premium'] = True
        save_data()
        
        emit('user_upgraded', {
            'username': username,
            'premium': True
        }, broadcast=True)

@socketio.on('send_friend_request')
def handle_send_friend_request(data):
    sender = data['from']
    receiver_input = data['to']
    
    # Find receiver
    receiver_email = None
    receiver_username = None
    
    if '@' in receiver_input:
        if receiver_input in users_db:
            receiver_email = receiver_input
            receiver_username = users_db[receiver_input]['username']
    else:
        for email, user_data in users_db.items():
            if user_data['username'] == receiver_input:
                receiver_email = email
                receiver_username = user_data['username']
                break
    
    if not receiver_username or receiver_username == sender:
        emit('friend_request_error', {'message': 'User not found'})
        return
    
    # Check if already friends
    sender_email = find_user_email(sender)
    if not sender_email:
        emit('friend_request_error', {'message': 'Sender not found'})
        return
    
    if 'friends' in users_db[sender_email] and receiver_username in users_db[sender_email]['friends']:
        emit('friend_request_error', {'message': 'Already friends'})
        return
    
    # Add friend request
    if 'friend_requests' not in users_db[receiver_email]:
        users_db[receiver_email]['friend_requests'] = []
    
    if sender not in users_db[receiver_email]['friend_requests']:
        users_db[receiver_email]['friend_requests'].append(sender)
    
    save_data()
    
    if receiver_username in active_users:
        emit('friend_request', {'from': sender}, room=active_users[receiver_username]['sid'])
    
    emit('friend_request_sent', {'to': receiver_username})

@socketio.on('get_friend_requests')
def handle_get_friend_requests():
    username = None
    for uname, user_data in active_users.items():
        if user_data['sid'] == request.sid:
            username = uname
            break
    
    if not username:
        return
    
    user_email = find_user_email(username)
    
    if user_email and 'friend_requests' in users_db[user_email]:
        requests = users_db[user_email]['friend_requests']
        emit('friend_requests_list', [{'from': r} for r in requests])
    else:
        emit('friend_requests_list', [])

@socketio.on('accept_friend_request')
def handle_accept_friend_request(data):
    receiver = data['to']
    sender = data['from']
    
    receiver_email = find_user_email(receiver)
    sender_email = find_user_email(sender)
    
    if not receiver_email or not sender_email:
        return
    
    # Add to friends list
    if 'friends' not in users_db[receiver_email]:
        users_db[receiver_email]['friends'] = []
    if sender not in users_db[receiver_email]['friends']:
        users_db[receiver_email]['friends'].append(sender)
    
    if 'friends' not in users_db[sender_email]:
        users_db[sender_email]['friends'] = []
    if receiver not in users_db[sender_email]['friends']:
        users_db[sender_email]['friends'].append(receiver)
    
    # Remove from friend requests
    if 'friend_requests' in users_db[receiver_email]:
        users_db[receiver_email]['friend_requests'] = [
            r for r in users_db[receiver_email]['friend_requests'] 
            if r != sender
        ]
    
    # Add to private chats
    for user_email, other_user in [(receiver_email, sender), (sender_email, receiver)]:
        if 'private_chats' not in users_db[user_email]:
            users_db[user_email]['private_chats'] = []
        
        chat_id = get_private_chat_id(receiver, sender)
        chat_info = {'chat_id': chat_id, 'with': other_user}
        
        if chat_info not in users_db[user_email]['private_chats']:
            users_db[user_email]['private_chats'].append(chat_info)
    
    save_data()
    
    if sender in active_users:
        emit('friend_request_accepted', {'username': receiver}, room=active_users[sender]['sid'])
        emit('private_chats_list', [
            {'id': get_private_chat_id(receiver, sender), 'username': receiver, 'unread': 0}
        ], room=active_users[sender]['sid'])
    
    if receiver in active_users:
        emit('friend_request_accepted', {'username': sender}, room=active_users[receiver]['sid'])
        emit('private_chats_list', [
            {'id': get_private_chat_id(receiver, sender), 'username': sender, 'unread': 0}
        ], room=active_users[receiver]['sid'])

@socketio.on('reject_friend_request')
def handle_reject_friend_request(data):
    receiver = data['to']
    sender = data['from']
    
    receiver_email = find_user_email(receiver)
    
    if not receiver_email:
        return
    
    if 'friend_requests' in users_db[receiver_email]:
        users_db[receiver_email]['friend_requests'] = [
            r for r in users_db[receiver_email]['friend_requests'] 
            if r != sender
        ]
    
    save_data()
    
    if sender in active_users:
        emit('friend_request_rejected', {'username': receiver}, room=active_users[sender]['sid'])

@socketio.on('get_friends')
def handle_get_friends():
    username = None
    for uname, user_data in active_users.items():
        if user_data['sid'] == request.sid:
            username = uname
            break
    
    if not username:
        return
    
    user_email = find_user_email(username)
    
    if not user_email or 'friends' not in users_db[user_email]:
        emit('friends_list', [])
        return
    
    friends_data = []
    for friend_username in users_db[user_email]['friends']:
        is_connected = friend_username in active_users
        
        is_premium = False
        friend_email = find_user_email(friend_username)
        if friend_email:
            is_premium = users_db[friend_email].get('premium', False)
        
        friends_data.append({
            'username': friend_username,
            'connected': is_connected,
            'premium': is_premium
        })
    
    emit('friends_list', friends_data)

@socketio.on('voice_status')
def handle_voice_status(data):
    username = data['username']
    muted = data.get('muted', False)
    
    if username in active_users:
        active_users[username]['user'].muted = muted
        
        active_users_list = []
        for uname, udata in active_users.items():
            active_users_list.append({
                'username': uname,
                'connected': True,
                'muted': udata['user'].get('muted', False),
                'speaking': udata['user'].get('speaking', False),
                'premium': users_db.get(find_user_email(uname), {}).get('premium', False)
            })
        
        emit('update_voice_users', {'users': active_users_list})

@socketio.on('start_voice')
def handle_start_voice(data):
    username = data['username']
    if username in active_users:
        active_users[username]['user'].speaking = True
        
        active_users_list = []
        for uname, udata in active_users.items():
            active_users_list.append({
                'username': uname,
                'connected': True,
                'muted': udata['user'].get('muted', False),
                'speaking': udata['user'].get('speaking', False),
                'premium': users_db.get(find_user_email(uname), {}).get('premium', False)
            })
        
        emit('update_voice_users', {'users': active_users_list})

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 SQUAD TALK - Full Featured Chat")
    print("=" * 60)
    print("\n🎯 Features:")
    print("✅ Original beautiful design restored")
    print("✅ Private chat between friends")
    print("✅ Server chat rooms")
    print("✅ Friend system with requests")
    print("✅ Premium upgrade with owner code")
    print("✅ Voice chat interface")
    print("✅ Message persistence")
    print("\n🔑 Owner Code: 'i'm the owner'")
    print("\n💾 Data saved to:", DATA_FILE)
    print("\n🚀 Access at: http://localhost:5000")
    print("=" * 60)
    
    socketio.run(app, 
                 host='0.0.0.0', 
                 port=5000, 
                 debug=True, 
                 allow_unsafe_werkzeug=True)

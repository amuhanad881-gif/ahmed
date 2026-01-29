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
                 debug=debug,
                 allow_unsafe_werkzeug=True)

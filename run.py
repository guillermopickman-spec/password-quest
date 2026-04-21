"""
Password Quest - Entry Point

Run the Flask development server.
For production, use a proper WSGI server like Gunicorn.
"""

import os
from app import create_app

# Create app instance
app = create_app(config_name=os.getenv("FLASK_ENV", "development"))

if __name__ == "__main__":
    # Development server
    debug_mode = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    port = int(os.getenv("PORT", 5000))
    host = os.getenv("HOST", "127.0.0.1")
    
    print(f"🎮 Password Quest starting at http://{host}:{port}")
    app.run(host=host, port=port, debug=debug_mode)
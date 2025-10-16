"""
WSGI entry point for Gunicorn
"""
from app import create_app

# Create Flask application
app = create_app()

if __name__ == "__main__":
    # For local development only
    app.run(host='0.0.0.0', port=8080, debug=True)

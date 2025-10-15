"""
Flask API Application for Figma Template Automation
"""
import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET', 'change-me-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 3600  # 1 hour

# CORS configuration
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5173", "http://localhost:3000"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# JWT configuration
jwt = JWTManager(app)

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per minute"]
)

# Import and register blueprints
from api import auth, templates, jobs

app.register_blueprint(auth.bp, url_prefix='/api/v1/auth')
app.register_blueprint(templates.bp, url_prefix='/api/v1/templates')
app.register_blueprint(jobs.bp, url_prefix='/api/v1/jobs')


@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'figma-template-automation-api',
        'version': '0.1.0'
    }), 200


@app.errorhandler(404)
def not_found(error):
    """404 error handler"""
    return jsonify({
        'error': {
            'code': 'NOT_FOUND',
            'message': 'The requested resource was not found'
        }
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """500 error handler"""
    return jsonify({
        'error': {
            'code': 'INTERNAL_ERROR',
            'message': 'An internal server error occurred'
        }
    }), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)

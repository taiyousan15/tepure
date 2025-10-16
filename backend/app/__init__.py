"""
Flask App Factory for Figma Template Automation API
"""
import os
import structlog
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


def create_app(config=None):
    """
    Application factory pattern

    Args:
        config: Optional configuration dictionary

    Returns:
        Configured Flask application
    """
    app = Flask(__name__)

    # Load configuration
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'change-me-in-production')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 900  # 15 minutes
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = 604800  # 7 days
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max request size

    if config:
        app.config.update(config)

    # CORS configuration
    CORS(app, resources={
        r"/api/*": {
            "origins": os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://localhost:3000').split(','),
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-Idempotency-Key"],
            "expose_headers": ["X-Request-ID"]
        }
    })

    # JWT configuration
    jwt = JWTManager(app)

    # Rate limiting with Redis or in-memory
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        storage_uri=os.getenv('REDIS_URL', 'memory://'),
        default_limits=["30 per minute"],
        strategy="fixed-window"
    )

    # Store limiter in app context for blueprint access
    app.limiter = limiter

    # Register blueprints
    from .api_v1 import api_v1_bp
    app.register_blueprint(api_v1_bp, url_prefix='/api/v1')

    # Health check endpoint
    @app.route('/health', methods=['GET'])
    def health_check():
        """
        Health check endpoint for load balancers

        Response:
            {
                "ok": true,
                "version": "1.0.0",
                "git": "abc123def"
            }
        """
        import subprocess

        # Get git commit hash
        git_hash = os.getenv('GIT_COMMIT', 'unknown')
        if git_hash == 'unknown':
            try:
                result = subprocess.run(
                    ['git', 'rev-parse', '--short', 'HEAD'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0:
                    git_hash = result.stdout.strip()
            except:
                pass

        return jsonify({
            'ok': True,
            'version': os.getenv('APP_VERSION', '1.0.0'),
            'git': git_hash
        }), 200

    # Error handlers
    @app.errorhandler(400)
    def bad_request(error):
        """400 Bad Request handler"""
        logger.warning("bad_request", error=str(error))
        return jsonify({
            'code': 'BAD_REQUEST',
            'message': 'Invalid request parameters'
        }), 400

    @app.errorhandler(401)
    def unauthorized(error):
        """401 Unauthorized handler"""
        logger.warning("unauthorized", error=str(error))
        return jsonify({
            'code': 'UNAUTHORIZED',
            'message': 'Authentication required'
        }), 401

    @app.errorhandler(403)
    def forbidden(error):
        """403 Forbidden handler"""
        logger.warning("forbidden", error=str(error))
        return jsonify({
            'code': 'FORBIDDEN',
            'message': 'Insufficient permissions'
        }), 403

    @app.errorhandler(404)
    def not_found(error):
        """404 Not Found handler"""
        logger.info("not_found", path=str(error))
        return jsonify({
            'code': 'NOT_FOUND',
            'message': 'Resource not found'
        }), 404

    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        """429 Rate Limit handler"""
        logger.warning("rate_limit_exceeded", error=str(error))
        return jsonify({
            'code': 'RATE_LIMIT_EXCEEDED',
            'message': 'Too many requests. Please try again later.'
        }), 429

    @app.errorhandler(500)
    def internal_error(error):
        """500 Internal Server Error handler"""
        logger.error("internal_error", error=str(error), exc_info=True)
        return jsonify({
            'code': 'INTERNAL_ERROR',
            'message': 'An internal server error occurred'
        }), 500

    logger.info("app_initialized", env=os.getenv('FLASK_ENV', 'production'))

    return app

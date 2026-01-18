
from flask import request, jsonify, render_template
from werkzeug.exceptions import HTTPException
from app.exceptions import BaseError

def handle_base_error(error):
    """Handle all custom exceptions"""
    # Check if request wants JSON
    if request.is_json or request.headers.get('Accept', '').startswith('application/json'):
        return jsonify(error.to_dict()), error.status_code
    else:
        return render_template("error.html", error=[error.status_code, error.message]), error.status_code

def handle_http_error(error):
    """Handle HTTP exceptions (404, 405, etc.)"""

    if request.is_json or request.headers.get('Accept', '').startswith('application/json'):
        return jsonify({"message": error.description, "status_code": error.code}), error.code
    else:
        return render_template("error.html", error=[error.code, error.description]), error.code

def handle_generic_error(error):
    """Handle unexpected exceptions"""
    if request.is_json or request.accept_mimetypes.accept_json:
        return jsonify({"message": f"Internal Server Error: {error}", "status_code": 500}), 500
    else:
        return render_template("error.html", error=[500, "Internal Server Error"]), 500

def register_error_handlers(app):
    """Register all error handlers with the Flask app"""
    app.register_error_handler(BaseError, handle_base_error)
    app.register_error_handler(HTTPException, handle_http_error)
    app.register_error_handler(Exception, handle_generic_error)
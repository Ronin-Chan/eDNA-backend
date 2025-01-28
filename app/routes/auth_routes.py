import uuid
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from app.models import User, Farm, Role
from app.database import db
import pytz
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.json
    required_fields = ['username', 'email', 'password', 'role_id']

    if not all(field in data for field in required_fields):
        return jsonify({"message": "Missing required fields"}), 400

    # Check if the email already exists in the database
    existing_user = User.query.filter_by(email=data['email']).first()
    if existing_user:
        return jsonify({"message": "Email is already registered"}), 400

    # Generate a unique user_id
    user_id = str(uuid.uuid4())

    # Hash the password
    hashed_password = generate_password_hash(data['password'])

    melbourne_tz = pytz.timezone('Australia/Melbourne')
    melbourne_time = datetime.now(melbourne_tz)

    # Create a new user instance
    new_user = User(
        user_id=user_id,
        username=data['username'],
        email=data['email'],
        password_hash=hashed_password,
        role_id=data['role_id'],
        farm_id=data.get('farm_id'),  # Use .get() to handle optional field
        created_at=melbourne_time
    )

    try:
        # Save to database
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "User registered successfully", "user_id": user_id}), 201
    except Exception as e:
        print(e)
        db.session.rollback()
        return jsonify({"message": str(e)}), 500

@auth_bp.route('/signin', methods=['POST'])
def signin():
    data = request.json

    # Validate request body
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({"message": "Email and password are required"}), 400

    email = data['email']
    password = data['password']

    # Query the database for the user
    user = User.query.filter_by(email=email).first()

    # Validate user existence and password
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"message": "Invalid email or password"}), 401

    # Create a JWT token for the user
    access_token = create_access_token(identity=user.user_id)
    
    role = Role.query.filter_by(role_id=user.role_id).first()
    farm = Farm.query.filter_by(farm_id=user.farm_id).first()

    # Return success response with user details and JWT token
    return jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "user": {
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
            "role_id": role.role_name,
            "role_name": role.role_name,
            "farm_id": user.farm_id,
            "farm_name": farm.farm_name if farm else None
        }
    }), 200
    
    

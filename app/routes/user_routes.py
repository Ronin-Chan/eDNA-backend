import uuid
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User, Role
from app.database import db

user_bp = Blueprint('user', __name__)

@user_bp.route('/editProfile', methods=['POST'])
def editProfile():
    data = request.json
    print(data)
    required_fields = ['user_id', 'username', 'email']
    if not all(field in data for field in required_fields):
        return jsonify({"message": "Missing required fields"}), 400

    user_id = data['user_id']
    username = data['username']
    email = data['email']

    # Query the database for the user
    user = User.query.filter_by(user_id=user_id).first()
    if not user:
        return jsonify({"message": "User not found"}), 404

    user.username = username
    user.email = email

    try:
        db.session.commit()
        return jsonify({"message": "User profile updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500


@user_bp.route('/changePassword', methods=['POST'])
def changePassword():
    data = request.json
    print(data)
    required_fields = ['user_id', 'current_password', 'new_password']
    if not all(field in data for field in required_fields):
        return jsonify({"message": "Missing required fields"}), 400

    user_id = data['user_id']
    current_password = data['current_password']
    new_password = data['new_password']

    # Query the database for the user
    user = User.query.filter_by(user_id=user_id).first()
    if not user:
        return jsonify({"message": "User not found"}), 404

    if not check_password_hash(user.password_hash, current_password):
        return jsonify({"message": "Current password is incorrect"}), 403

    user.password_hash = generate_password_hash(new_password)

    try:
        db.session.commit()
        return jsonify({"message": "Password updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500
    
# get all farmers
@user_bp.route('/getFarmers', methods=['GET'])
def getFarmers():
    roleId = Role.query.filter_by(role_name='Farmer').first().role_id
    
    farms = User.query.filter_by(role_id=roleId).all()
    if not farms:
        return jsonify({"message": "No farmers found"}), 404
      
    return jsonify([farm.to_dict() for farm in farms]), 200
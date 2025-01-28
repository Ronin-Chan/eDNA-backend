from flask import Blueprint, jsonify
from app.models import Role

role_bp = Blueprint('role', __name__)

@role_bp.route('/roles', methods=['GET'])
def getRoles():
    roles = Role.query.all()
    return jsonify([{"id": role.role_id, "name": role.role_name} for role in roles]), 200
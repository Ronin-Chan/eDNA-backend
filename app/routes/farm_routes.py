from flask import Blueprint, request, jsonify
from app.models import Farm
import uuid
import pytz
from datetime import datetime
from app.database import db

farm_bp = Blueprint('farm', __name__)

@farm_bp.route('/farms', methods=['GET'])
def getFarms():
    farms = Farm.query.all()
    return jsonify([{"farm_id": farm.farm_id, "farm_name": farm.farm_name} for farm in farms]), 200

@farm_bp.route('/create', methods=['POST'])
def createFarm():
    data = request.json
    required_fields = ['farm_name', 'location', 'gs1_company_prefix', 'farm_gln']
    if not all(field in data for field in required_fields):
        return jsonify({"message": "Missing required fields"}), 400
    
    # Check if the farm name already exists in the database
    existing_farm = Farm.query.filter_by(farm_name=data['farm_name']).first()
    if existing_farm:
        return jsonify({"message": "Farm name is already registered"}), 400
    
    farm_id = str(uuid.uuid4())
    
    melbourne_tz = pytz.timezone('Australia/Melbourne')
    melbourne_time = datetime.now(melbourne_tz)
    
    farm_name = data['farm_name']
    
    new_farm = Farm(
        farm_id=farm_id,
        farm_name=farm_name,
        location=data['location'],
        gs1_company_prefix=data['gs1_company_prefix'],
        farm_gln=data['farm_gln'],
        created_at=melbourne_time
    )
    
    try:
        db.session.add(new_farm)
        db.session.commit()
        return jsonify({"farm_id": farm_id, "farm_name": farm_name}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500
    
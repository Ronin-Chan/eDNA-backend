from app.database import db
from datetime import datetime
import uuid

class Apiary(db.Model):
    __tablename__ = 't_apiary'

    apiary_id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # Auto-incrementing primary key
    apiary = db.Column(db.String(255), nullable=False)  # Apiary name
    location = db.Column(db.String(2), nullable=False)  # Location (country code)
    gs1_company_prefix = db.Column(db.String(255), nullable=True)  # GS1 company prefix (optional)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # Creation timestamp

    def __repr__(self):
        return f"<Apiary {self.apiary}>"


class Farm(db.Model):
    __tablename__ = 't_farm'

    farm_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))  # CHAR(36) for UUID
    farm_name = db.Column(db.String(255), nullable=False)  # Farm name
    location = db.Column(db.String(255), nullable=False)  # Location (country code)
    farm_gln = db.Column(db.String(255), nullable=True)  # GLN (optional)
    gs1_company_prefix = db.Column(db.String(255), nullable=True)  # GS1 prefix (optional)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # Creation timestamp

    # Relationships
    users = db.relationship('User', backref='farm', lazy=True)  # One-to-many relationship with User
    files = db.relationship('File', backref='farm', lazy=True)  # One-to-many relationship with File

    def __repr__(self):
        return f"<Farm {self.farm_name}>"


class File(db.Model):
    __tablename__ = 't_file'

    file_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))  # CHAR(36) for UUID
    pair_id = db.Column(db.String(36), nullable=True)  # Pair ID (optional)
    hive_giai = db.Column(db.String(255), nullable=True)  # Hive GIAI (optional)
    file_type = db.Column(db.String(255), nullable=False)  # File type
    file_name = db.Column(db.String(255), nullable=False)  # File name
    file_url = db.Column(db.String(2048), nullable=False)  # File URL
    user_id = db.Column(db.String(36), db.ForeignKey('t_user.user_id'), nullable=True)  # Foreign key to User
    farm_id = db.Column(db.String(36), db.ForeignKey('t_farm.farm_id'), nullable=True)  # Foreign key to Farm
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # Creation timestamp

    def __repr__(self):
        return f"<File {self.file_name}>"


class Role(db.Model):
    __tablename__ = 't_role'

    role_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    role_name = db.Column(db.String(255), nullable=False, unique=True)

    def __repr__(self):
        return f"<Role {self.role_name}>"


class User(db.Model):
    __tablename__ = 't_user'

    user_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))  # CHAR(36) for UUID
    username = db.Column(db.String(255), nullable=False)  # Username
    role_id = db.Column(db.Integer, db.ForeignKey('t_role.role_id'), nullable=False)  # Foreign key to Role
    email = db.Column(db.String(255), unique=True, nullable=False)  # Unique email
    password_hash = db.Column(db.String(255), nullable=False)  # Hashed password
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # Creation timestamp
    farm_id = db.Column(db.String(36), db.ForeignKey('t_farm.farm_id'), nullable=True)  # Foreign key to Farm

    # Relationships
    files = db.relationship('File', backref='user', lazy=True)  # One-to-many relationship with File
    role = db.relationship('Role', backref='users', lazy=True)  # Many-to-one relationship with Role

    def __repr__(self):
        return f"<User {self.username}>"

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "username": self.username,
            "role_id": self.role_id,
            "email": self.email,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "farm_id": self.farm_id,
        }

class Visualization(db.Model):
    __tablename__ = 't_visualization'

    visualization_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))  # CHAR(36) for UUID
    pair_id = db.Column(db.String(36), nullable=True)
    metadata_file_id = db.Column(db.String(36), nullable=True)
    barcoding_file_id = db.Column(db.String(36), nullable=True)
    farm_id = db.Column(db.String(36), db.ForeignKey('t_farm.farm_id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # Creation timestamp
    
    def __repr__(self):
        return f"<Visualization {self.file_name}>"
    
class VisualizationPermisson(db.Model):
    __tablename__ = 't_visualization_permission'

    visualization_permission_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))  # CHAR(36) for UUID
    visualization_id = db.Column(db.String(36), db.ForeignKey('t_visualization.visualization_id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('t_user.user_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # Creation timestamp
    
    def __repr__(self):
        return f"<VisualizationPermission {self.visualization_permission_id}>"
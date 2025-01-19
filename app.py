# app.py

from flask import Flask, request, jsonify
from models import db, User, Role, Permission
from intents import detect_intent, INTENT_PERMISSION_MAP
import os

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
database_path = os.path.join(basedir, 'rbac.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + database_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Inisialisasi database secara manual
with app.app_context():
    db.create_all()

# Rute Root
@app.route('/', methods=['GET'])
def home():
    return jsonify({'message': 'RBAC Application Running'}), 200

# Endpoint untuk Menambah User
@app.route('/users', methods=['POST'])
def add_user():
    if not request.is_json:
        return jsonify({'message': 'Request must be JSON'}), 400
    data = request.get_json()
    username = data.get('username')
    if not username:
        return jsonify({'message': 'Username is required'}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'User already exists'}), 400
    user = User(username=username)
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': f'User {username} created', 'user_id': user.id}), 201

# Endpoint untuk Mengambil Detail User
@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    roles = [role.name for role in user.roles]
    return jsonify({'id': user.id, 'username': user.username, 'roles': roles}), 200

# Endpoint untuk Menambah Role
@app.route('/roles', methods=['POST'])
def add_role():
    if not request.is_json:
        return jsonify({'message': 'Request must be JSON'}), 400
    data = request.get_json()
    role_name = data.get('name')
    if not role_name:
        return jsonify({'message': 'Role name is required'}), 400
    if Role.query.filter_by(name=role_name).first():
        return jsonify({'message': 'Role already exists'}), 400
    role = Role(name=role_name)
    db.session.add(role)
    db.session.commit()
    return jsonify({'message': f'Role {role_name} created', 'role_id': role.id}), 201

# Endpoint untuk Mengambil Detail Role
@app.route('/roles/<int:role_id>', methods=['GET'])
def get_role(role_id):
    role = Role.query.get(role_id)
    if not role:
        return jsonify({'message': 'Role not found'}), 404
    permissions = [perm.name for perm in role.permissions]
    return jsonify({'id': role.id, 'name': role.name, 'permissions': permissions}), 200

# Endpoint untuk Menambah Permission
@app.route('/permissions', methods=['POST'])
def add_permission():
    if not request.is_json:
        return jsonify({'message': 'Request must be JSON'}), 400
    data = request.get_json()
    permission_name = data.get('name')
    if not permission_name:
        return jsonify({'message': 'Permission name is required'}), 400
    if Permission.query.filter_by(name=permission_name).first():
        return jsonify({'message': 'Permission already exists'}), 400
    permission = Permission(name=permission_name)
    db.session.add(permission)
    db.session.commit()
    return jsonify({'message': f'Permission {permission_name} created', 'permission_id': permission.id}), 201

# Endpoint untuk Mengambil Detail Permission
@app.route('/permissions/<int:permission_id>', methods=['GET'])
def get_permission(permission_id):
    permission = Permission.query.get(permission_id)
    if not permission:
        return jsonify({'message': 'Permission not found'}), 404
    return jsonify({'id': permission.id, 'name': permission.name}), 200

# Endpoint untuk Mengaitkan Role ke User
@app.route('/users/<int:user_id>/roles', methods=['POST'])
def assign_role_to_user(user_id):
    if not request.is_json:
        return jsonify({'message': 'Request must be JSON'}), 400
    data = request.get_json()
    role_id = data.get('role_id')
    if not role_id:
        return jsonify({'message': 'role_id is required'}), 400
    user = User.query.get(user_id)
    role = Role.query.get(role_id)
    if not user or not role:
        return jsonify({'message': 'User or Role not found'}), 404
    if role in user.roles:
        return jsonify({'message': f'User already has role {role.name}'}), 400
    user.roles.append(role)
    db.session.commit()
    return jsonify({'message': f'Role {role.name} assigned to user {user.username}'}), 200

# Endpoint untuk Mengaitkan Permission ke Role
@app.route('/roles/<int:role_id>/permissions', methods=['POST'])
def assign_permission_to_role(role_id):
    if not request.is_json:
        return jsonify({'message': 'Request must be JSON'}), 400
    data = request.get_json()
    permission_id = data.get('permission_id')
    if not permission_id:
        return jsonify({'message': 'permission_id is required'}), 400
    role = Role.query.get(role_id)
    permission = Permission.query.get(permission_id)
    if not role or not permission:
        return jsonify({'message': 'Role or Permission not found'}), 404
    if permission in role.permissions:
        return jsonify({'message': f'Role already has permission {permission.name}'}), 400
    role.permissions.append(permission)
    db.session.commit()
    return jsonify({'message': f'Permission {permission.name} assigned to role {role.name}'}), 200

# Endpoint untuk Mengecek Akses User Berdasarkan Input Teks
@app.route('/check_access', methods=['POST'])
def check_access():
    if not request.is_json:
        return jsonify({'message': 'Request must be JSON'}), 400
    data = request.get_json()
    username = data.get('username')
    user_input = data.get('input_text')
    
    if not username or not user_input:
        return jsonify({'message': 'Username and input_text are required'}), 400

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'message': 'User not found'}), 404

    intent = detect_intent(user_input)
    if not intent:
        return jsonify({'message': 'Intent not recognized'}), 400

    # Dapatkan permission yang dibutuhkan berdasarkan intent
    required_permissions = INTENT_PERMISSION_MAP.get(intent, [])

    # Dapatkan semua permission yang dimiliki user melalui role
    user_permissions = set()
    for role in user.roles:
        for perm in role.permissions:
            user_permissions.add(perm.name)

    # Cek apakah user memiliki semua required permissions
    has_access = all(perm in user_permissions for perm in required_permissions)

    return jsonify({
        'username': username,
        'input_text': user_input,
        'intent': intent,
        'required_permissions': required_permissions,
        'user_permissions': list(user_permissions),
        'has_access': has_access
    }), 200

if __name__ == '__main__':
    app.run(debug=True)
from app.auth import bp as api
from app.models import User, TokenBlacklist
from app import jwt, db
from flask import jsonify, request, current_app
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import (
    jwt_required, get_jwt_identity, jwt_refresh_token_required
)
from app.auth.helpers import (
    add_token_to_database, is_token_revoked,
    get_user_tokens, revoke_token, unrevoke_token, TokenNotFound,
    create_tokens, add_role
)

@jwt.token_in_blacklist_loader
def check_if_token_revoked(decoded_token):
    return is_token_revoked(decoded_token)

@api.route('/auth/login', methods=['POST'])
def login():

    data = request.get_json()
    email, password = data['email'], data['password']
    user = User.query.filter_by(email=email).first()

    if user is None or not user.check_password(password):
        return jsonify({'msg': 'No user found or incorrect password'}), 404

    tokens = create_tokens(user)

    return jsonify(tokens), 200

@api.route('/auth/register', methods=['POST'])
def register():

    data = request.get_json()

    password = data.pop('password')
    
    new_user = User(**data)
    new_user.create_password(password)
    db.session.add(new_user)

    add_role(new_user, data)

    #Just in case email already exists
    try:
        db.session.commit()
    except IntegrityError:
        return jsonify({'msg': 'Email already exists'}), 400

    tokens = create_tokens(new_user)

    return jsonify(tokens), 201

@api.route('/auth/register/teacher', methods=['POST'])
def register_teacher():
    data = request.get_json()

    teacher_data = {
        github: data.get('github', None),
        subject: data['subject'],
        link_to_resume: data.get('resume', None)
    }

    user_data = {
        first: data['first'],
        last: data['last'],
        email: data['email'],
        location: data['location']
    }

@api.route('/auth/tokens', methods=['GET'])
@jwt_required
def get_tokens():
    #User must send header with format Authorization: Bearer <JWT> 
    user_identity = get_jwt_identity()
    tokens = get_user_tokens(user_identity)
    return jsonify([token.json_response() for token in tokens]), 200

@api.route('/auth/tokens/all', methods=['GET'])
def get_all_tokens():
    tokens = TokenBlacklist.query.all()
    return jsonify([token.json_response() for token in tokens])

@api.route('/auth/refresh', methods=['POST'])
@jwt_refresh_token_required
def refresh():
    #User must provide authorization header with Bearer <JWT> 
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    access_token = create_access_token(identity=user.id, user_claims=user.json_response())
    add_token_to_database(access_token, current_app.config['JWT_IDENTITY_CLAIM'])

    return jsonify({'access_token': access_token}), 201

@api.route('/auth/logout', methods=['POST'])
@jwt_refresh_token_required #refresh lasts longer than access
def logout():
    #user must provide JWT in authorization
    user_identity = get_jwt_identity()
    try:
        revoke_token(user_identity)
    except TokenNotFound:
        return jsonify({'msg': 'No such token'}), 400
    return jsonify({'msg': 'Successfully logged out and revoked token'}), 200




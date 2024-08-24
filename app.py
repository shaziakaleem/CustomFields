from flask import Flask, request,jsonify

from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager,create_access_token,jwt_required,get_jwt_identity
from marshmallow import Schema,fields,validate,ValidationError
import bcrypt
from sqlalchemy.orm import relationship

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///custom_fields_new.db'
app.config['JWT_SECRET_KEY'] = 'your_wjt_secret_key'
db = SQLAlchemy(app)
jwt = JWTManager(app)

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    users = relationship('User', back_populates='role')

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    role = relationship('Role', back_populates='users')

class CustomField(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(255),nullable=False)
    type = db.Column(db.String(50),nullable= False)
    options = db.Column(db.Text) #JSON options

class CustomFieldValue(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    custom_field_id = db.Column(db.Integer,db.ForeignKey('custom_field.id'),nullable=False)
    entity_id = db.Column(db.Integer,nullable= False)
    value = db.Column(db.Text)

#Schemas
class CustomFieldSchema(Schema):
    name = fields.String(required=True)
    type = fields.String(required=True,validate=validate.OneOf(['text', 'number', 'date', 'dropdown', 'boolean']))
    options = fields.String()

class CustomFieldValueSchema(Schema):
    custom_field_id = fields.Integer(required = True)
    entity_id = fields.Integer(required=True)
    value = fields.String()

class UserSchema(Schema):
    username = fields.String(required=True)
    password = fields.String(required=True)

#Create database tables
@app.before_first_request
def create_tables():
    db.create_all()


#Authentication and Authorization
@app.route('/api/register',methods = ['POST'])
def register():
    data = request.get_json()
    username = data['username']
    password = data['password']
    role_name = data['role']
    
    role = Role.query.filter_by(name=role_name).first()
    if not role:
        return jsonify({"msg": "Role does not exist"}), 400
    
    new_user = User(username=username, password=password, role=role)
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({"msg": "User created"}), 201


@app.route('/api/login',methods =['POST'])
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']
    
    user = User.query.filter_by(username=username, password=password).first()
    if not user:
        return jsonify({"msg": "Bad username or password"}), 401
    
    access_token = create_access_token(identity=username)
    return jsonify(access_token=access_token)

def check_role(required_role):
    def wrapper(fn):
        @jwt_required()
        def decorated_function(*args,**kwargs):
            current_user = get_jwt_identity()
            user = User.query.filter_by(username=current_user).first()
            if not user or user.role.name != required_role:
                return {'msg': 'Forbidden'}, 403
            return fn(*args, **kwargs)
        return decorated_function
    return wrapper

@app.route('/api/register-role', methods=['POST'],endpoint='register_role')
# @check_role('admin')
def register_role():
    data = request.get_json()
    role_name = data.get('name')
    
    if not role_name:
        return jsonify({"msg": "Role name is required"}), 400
    
    existing_role = Role.query.filter_by(name=role_name).first()
    if existing_role:
        return jsonify({"msg": "Role already exists"}), 400
    
    new_role = Role(name=role_name)
    db.session.add(new_role)
    db.session.commit()
    
    return jsonify({"msg": "Role created", "role": role_name}), 201

#CRUD Endpoints

@app.route('/api/custom-fields', methods=['POST'],endpoint='create_custom_fields')
@jwt_required()
@check_role('admin')
def create_custom_fields():
    schema = CustomFieldSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as err:
        return jsonify(err.messages), 400
    new_field = CustomField(
        name=data['name'],
        type=data['type'],
        options=data.get('options')
    )
    db.session.add(new_field)
    db.session.commit()
    return jsonify({'id': new_field.id, 'name': new_field.name, 'type': new_field.type, 'options': new_field.options}), 201


@app.route('/api/custom-fields/<int:id>', methods=['GET'])
@jwt_required()
def get_custom_field(id):
    field = CustomField.query.get_or_404(id)
    return jsonify({'id': field.id, 'name': field.name, 'type': field.type, 'options': field.options})

@app.route('/api/custom-fields/update/<int:id>', methods=['PUT'], endpoint='update_custom_field')
@jwt_required()
@check_role('admin')
def update_custom_field(id):
    schema = CustomFieldSchema()
    field = CustomField.query.get_or_404(id)
    try:
        data = schema.load(request.get_json())
    except ValidationError as err:
        return jsonify(err.messages), 400
    field.name = data['name']
    field.type = data['type']
    field.options = data.get('options')
    db.session.commit()
    return jsonify({'id': field.id, 'name': field.name, 'type': field.type, 'options': field.options})

@app.route('/api/custom-fields/delete/<int:id>', methods=['DELETE'], endpoint='delete_custom_field')
@jwt_required()
@check_role('admin')
def delete_custom_field(id):
    field = CustomField.query.get_or_404(id)
    db.session.delete(field)
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/api/custom-field-values', methods=['POST'])
@jwt_required()
def create_custom_field_value():
    schema = CustomFieldValueSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as err:
        return jsonify(err.messages), 400
    new_value = CustomFieldValue(
        custom_field_id=data['custom_field_id'],
        entity_id=data['entity_id'],
        value=data['value']
    )
    db.session.add(new_value)
    db.session.commit()
    return jsonify({'id': new_value.id, 'custom_field_id': new_value.custom_field_id, 'entity_id': new_value.entity_id, 'value': new_value.value}), 201

@app.route('/api/custom-field-values', methods=['GET'])
@jwt_required()
def get_custom_field_values():
    entity_id = request.args.get('entity_id')
    values = CustomFieldValue.query.filter_by(entity_id=entity_id).all()
    result = [{'custom_field_id': v.custom_field_id, 'value': v.value} for v in values]
    return jsonify(result)

@app.route('/api/custom-field-values/<int:id>', methods=['DELETE'],endpoint='delete_custom_field_value')
@jwt_required()
@check_role('admin')
def delete_custom_field_value(id):
    value = CustomFieldValue.query.get_or_404(id)
    db.session.delete(value)
    db.session.commit()
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(debug=True)
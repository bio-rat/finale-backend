from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, \
    jsonify, current_app
from sqlalchemy.orm.exc import NoResultFound

from flask_login import current_user, login_required, login_user, logout_user
from app import db
# from app.main.forms import EditProfileForm, PostForm, SearchForm, MessageForm
from app.models import User, Token, House
from app.main import bp
import uuid


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
def index():
    return 'hello there'

@bp.route('/agentslist', methods=['GET', 'POST'])
def agents():
    if request.method == 'GET':
        queryAgents = User.query.filter_by(is_broker=True).all()
        agentsList = []
        for x in queryAgents:
            agentsList.append({
                "username": x.username,
                "imgurl": x.imgurl,
                "user_id": x.id
            })
        print(agentsList)
        return jsonify({
            "agentsList": agentsList
        })

@bp.route('/profile/<int:user_id>', methods=['GET', 'POST'])
def profile(user_id):
    if request.method == 'GET':
        user = User.query.filter_by(id=user_id).first()
        
        return jsonify({
            "username": user.username,
            "imgurl": user.imgurl
        })

@bp.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        x = request.get_json()

        email = x['email']
        password = x['password']

        user = User.query.filter_by(email=email).first()

        if user is not None and user.check_password(password):
            login_user(user)
            db.session.commit()

            token_query = Token.query.filter_by(user_id=current_user.id)

            try:
                token = token_query.one()
            except NoResultFound:
                token = Token(user_id=current_user.id, uuid=str(uuid.uuid4().hex))  

                db.session.add(token)
                db.session.commit()
            
            # return redirect("http://localhost:3000/?api_key={}".format(token.uuid))

            return jsonify({
                "success": True,
                "email": email,
                "username": current_user.username,
                "imgurl": current_user.imgurl,
                "token": token.uuid,
                "is_broker": current_user.is_broker,
                "user_id": current_user.id
            }), 201
        else:
            return jsonify({
                "success": False,
                "message": "wrong password my dude"
            }), 400

@bp.route('/logout', methods=['GET'])
def logout():
    Token.query.filter_by(user_id=current_user.id).delete()

    db.session.commit()

    logout_user()
    return jsonify({
                "success": True,
                "message": "You've successfully logged out!",
            }), 201

@bp.route('/signup', methods=['POST'])
def signup():
    if request.method == 'POST':
        x = request.get_json()

        if not x['email'] or not x['username'] or not x['password']:
            return jsonify({
                "success": False,
                'message': "please fill in all the fields"
            }), 400
        else:
            email = x['email']
            password = x['password']
            username = x['username']
            imgurl = x['imgurl']
            is_broker = x['is_broker']

            if User.query.filter_by(email=email).first():
                return jsonify({
                    "success": False,
                    'message': "email already exist"
                }), 400
            elif User.query.filter_by(username=username).first():
                return jsonify({
                    "success": False,
                    'message': "username already exist"
                }), 400
            else:
                user = User(username=username, email=email, imgurl=imgurl, is_broker=is_broker)
                user.set_password(password)
                
                db.session.add(user)
                db.session.commit()

                return jsonify({
                    "success": True,
                    'message': "Successfully Sign Up",
                    "is_broker": is_broker
                }), 200


@bp.route('/sell', methods=['POST'])
def sell():
    if request.method == 'POST':
        x = request.get_json()

        if not x['address'] or not x['city'] or not x['district'] or not x['ward'] or not x['street'] or not x['number']:
            return jsonify({
                "success": False,
                'message': "please fill in all the fields"
            }), 400
        else:
            address = x['address']
            city = x['city'] 
            district = x['district'] 
            ward = x['ward'] 
            street = x['street'] 
            number = x['number']

            house = House(address=address, city=city, district=district, ward=ward, street=street, number=number, user_id=current_user.id)
            
            db.session.add(house)
            db.session.commit()

            return jsonify({
                "success": True,
                'message': "Successfully list your house"
            }), 200

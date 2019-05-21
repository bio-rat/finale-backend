from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, jsonify, current_app
from sqlalchemy.orm.exc import NoResultFound

from flask_login import current_user, login_required, login_user, logout_user
from app import db, socketio
# from app.main.forms import EditProfileForm, PostForm, SearchForm, MessageForm
from app.models import User, Token, House, Message
from app.main import bp
import uuid
from flask_socketio import join_room, leave_room, send


# Home route: just to check if it's online
@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
def index():
    return '<span style="color: red">API SERVER IS ONLINE</span>'

# Get the full list of Agents 
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
        return jsonify({
            "agentsList": agentsList
        })

# Get the contact list
@bp.route('/contactlist', methods=['GET', 'POST'])
def contactlist():
    if request.method == 'GET':

        # get all the houses that are connected to brokers
        chosenHouses = db.session.query(User, House).outerjoin(House, User.id == House.broker_id).filter(House.broker_id.isnot(None), House.user_id == 10).all()

        contactList = []

        for x in chosenHouses:
            contactList.append({
                "username": x[0].username,
                "imgurl": x[0].imgurl,
                "user_id": x[0].id,
                "room_id": x[1].room_id,
                "address": x[1].address
            })

        return jsonify({
            "contactList": contactList
        })

# Profile for each user
@bp.route('/profile/<int:user_id>', methods=['GET', 'POST'])
def profile(user_id):
    if request.method == 'GET':
        user = User.query.filter_by(id=user_id).first()
        
        return jsonify({
            "username": user.username,
            "imgurl": user.imgurl,
        })

# Get houses list
@bp.route('/houseslist', methods=['GET', 'POST'])
def houseslist():
    if request.method == 'GET':

        # get all houses from this user
        all_houses = House.query.filter_by(user_id=current_user.id).all()

        housesList = []

        for x in all_houses:
            housesList.append({
                "address": x.address,
                "house_id": x.id,
                "is_chosen": x.is_chosen()
            })
        
        return jsonify({
            "housesList": housesList
        })

# Login route
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
            
            return jsonify({
                "success": True,
                "email": email,
                "username": current_user.username,
                "imgurl": current_user.imgurl,
                "token": token.uuid,
                "is_broker": current_user.is_broker,
                "user_id": current_user.id,
            }), 201
        else:
            return jsonify({
                "success": False,
                "message": "wrong password my dude"
            }), 400

# Logout route
@bp.route('/logout', methods=['GET'])
def logout():
    Token.query.filter_by(user_id=current_user.id).delete()

    db.session.commit()

    logout_user()
    return jsonify({
                "success": True,
                "message": "You've successfully logged out!",
            }), 201

# Signup route
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

# This route helps to list the houses information to database
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

# this route helps to connect a broker to a house
@bp.route('/chooseAgent', methods=['POST'])
def chooseAgent():
    if request.method == 'POST':
        x = request.get_json()

        house_id = x['house_id']
        broker_id = x['broker_id'] 
        
        house = House.query.filter_by(id=house_id).first()
        house.broker_id = broker_id

        # set room id by model method
        house.set_roomid(broker_id)

        db.session.add(house)
        db.session.commit()

        return jsonify({
            "success": True,
            'message': "Successfully choose this agent"
        }), 200


@socketio.on('join')
def on_join(data):
    room = data['room_id']
    join_room(room)

@socketio.on('leave')
def on_leave(data):
    room = data['room_id']
    leave_room(room)

@socketio.on('my_message')
def handle_receive_msg(data):
    print('received message: ' + "user_id: " + str(data['user_id']) + " message: " + str(data['message']), " from room: " + str(data['room_id']))

    # message = Message(text=message)
    # db.session.add(message)
    # db.session.commit()

    socketio.emit('back_message', {"message": data['message']},  room=data['room_id'])
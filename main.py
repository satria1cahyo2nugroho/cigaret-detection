
from urllib import response
from flask import Flask,send_file,render_template, request, redirect, url_for,request
from flask_restx import Resource, Api, reqparse
from flask_cors import CORS
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
import os, subprocess
import cv2


app = Flask(__name__) # Flask object instantiation..
CORS(app ,supports_credentials=True)
api = Api(app) # Flask-restx object instantiation..


####################
# BEGIN: Database #
##################
from flask_sqlalchemy import SQLAlchemy


app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://localhost:@127.0.0.1:3306/flask"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True

db = SQLAlchemy(app) # SQLAlchemy object instantiation.

class User(db.Model):
	id		= db.Column(db.Integer(), primary_key=True, nullable=False)
	email	= db.Column(db.String(32), unique=True, nullable=False)
	name	= db.Column(db.String(64), nullable=False)
	password= db.Column(db.String(256), nullable=False)
##################pipenv
# END: Database #
################



#####################################
# BEGIN: User Registration & Login #
###################################
import base64
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import jwt


parser4SignUp = reqparse.RequestParser()
parser4SignUp.add_argument('email', type=str, location='json', 
	required=True, help='Email Address')
parser4SignUp.add_argument('name', type=str, location='json', 
	required=True, help='Fullname')
parser4SignUp.add_argument('password', type=str, location='json', 
	required=True, help='Password')
parser4SignUp.add_argument('re_password', type=str, location='json', 
	required=True, help='Retype Password')

@api.route('/signup')
class Registration(Resource):
	@api.expect(parser4SignUp)
	def post(self):
		args 		= parser4SignUp.parse_args()
		email 		= args['email']
		name 		= args['name']
		password 	= args['password']
		rePassword 	= args['re_password']

		if password != rePassword:
			return {
				'message': 'Password is not the same!'
			}, 400 # HTTP Status Code for Bad Request.

		user = db.session.execute(db.select(User).filter_by(email=email)).first()
		if user:
			return {
				'message': 'This email address has been used!'
			}, 409 # HTTP Status Code for "Conflict".

		user 			= User() # User instantiation.
		user.email 		= email
		user.name 		= name
		user.password 	= generate_password_hash(password)

		db.session.add(user)
		db.session.commit()

		return {
			'messsage': 'Successful'
		}, 201 # HTTP Status Code for "Created"


###################################################################################
SECRET_KEY 		= "WhatEverYouWant!"
ISSUER 			= "myFlaskWebservice"
AUDIENCE_MOBILE = "myMobileApp"
 

import base64
##################################################
# BEGIN: Example of Bearer/Token Authentication #
################################################
parser4Bearer = reqparse.RequestParser()
parser4Bearer.add_argument('Authorization', type=str, location='headers', required=True, 
	help='Please read https://swagger.io/docs/specification/authentication/bearer-authentication/')

@api.route('/bearer-auth')
class BearerAuth(Resource):
	@api.expect(parser4Bearer)
	def post(self):
		args 		= parser4Bearer.parse_args()
		bearerAuth 	= args['Authorization']
		# bearerAuth is "Bearer yourjwttokenyourjwttokenyourjwttokenyourjwttokenyourjwttoken"
		jwtToken 	= bearerAuth[7:] # Remove first-7 digits (remove "Bearer ").
		# jwtToken is "yourjwttokenyourjwttokenyourjwttokenyourjwttokenyourjwttoken"
		try:
			payload = jwt.decode(
				jwtToken,
				SECRET_KEY,
				audience = [AUDIENCE_MOBILE],
				issuer = ISSUER,
				algorithms = ['HS256'],
				options = {"require": ["aud", "iss", "iat", "exp"]}
			)
		except:
			return {'message': 'Unauthorized! Token is invalid! Please, sign in!'}, 401

		return {'message': 'Token is valid!'}, 200
################################################
# END: Example of Bearer/Token Authentication #
##############################################
def decodetoken(jwtToken):
    decode_result = jwt.decode(jwtToken,
				SECRET_KEY,
				audience = [AUDIENCE_MOBILE],
				issuer = ISSUER,
				algorithms = ['HS256'],
				options = {"require": ["aud", "iss", "iat", "exp"]})	
    return decode_result

#####################################################################################
parser4SignIn = reqparse.RequestParser()
parser4SignIn.add_argument('email', type=str, location='json', 
	required=True, help='Email Address')
parser4SignIn.add_argument('password', type=str, location='json', 
	required=True, help='Password')


@api.route('/signin')
class LogIn(Resource):
	@api.expect(parser4SignIn)
	def post(self):
		args 		= parser4SignIn.parse_args()
		email 		= args['email']
		password 	= args['password']
		
		if not email or not password:
			return {
				'message': 'Please type email and password!'
			}, 400

		user = db.session.execute(db.select(User).filter_by(email=email)).first()
		if not user:
			return {
				'message': 'Wrong email or password!'
			}, 400
		else:
			user = user[0] # Unpack the array

		if check_password_hash(user.password, password):
			payload = {
				'user_id': user.id,
				'email': user.email,
				'aud': AUDIENCE_MOBILE,
				'iss': ISSUER,
				'iat': datetime.utcnow(),
				'exp': datetime.utcnow() + timedelta(hours=2)
			}
			token = jwt.encode(payload, SECRET_KEY)
			return {'token': token}, 200
		else:
			return {'message': 'Wrong email or password!'}, 400





authParser = reqparse.RequestParser()
authParser.add_argument('Authorization', type=str, help='Authorization', location='headers', required=True)
#@api.route('/user')
#class DetailUser(Resource):
#       @api.expect(authParser)
#       def get(self):
#	       args = authParser.parse_args()
#	       bearerAuth  = args['Authorization']
#	       try:
#		       jwtToken    = bearerAuth[7:]
#		       token = decodetoken(jwtToken)
#		       user =  db.session.execute(db.select(User).filter_by(email=token['user_email'])).first()
#		       user = user[0]
#		       data = {
#			       'name' : user.name,
#				   'email' : user.email
#           }
#		       except:
#		       return {
#			       'message' : 'Token Tidak valid,Silahkan Login Terlebih Dahulu!'}, 401
#		       return data {'message' : 'melihat data User Sukses'}, 200
       
editParser = reqparse.RequestParser()
editParser.add_argument('email', type=str, help='email', location='json', required=True)
editParser.add_argument('name', type=str, help='name', location='json', required=True)
editParser.add_argument('Authorization', type=str, help='Authorization', location='headers', required=True)
@api.route('/edituser')
class EditUser(Resource):
       @api.expect(editParser)
       def put(self):
        args = editParser.parse_args()
        bearerAuth  = args['Authorization']
        email = args['email']
        name = args['name']
        datenow =  datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        try:
            jwtToken    = bearerAuth[7:]
            token = decodetoken(jwtToken)
            # print(token.get)
            user = User.query.filter_by(email=token.get('email')).first()
            user.email = email
            user.name = name
            user.updatedAt = datenow
            db.session.commit()
        except:
            return {
                'message' : 'Token Tidak valid,Silahkan Login Terlebih Dahulu!'
            }, 401
        return {'message' : 'Update User Sukses'}, 200

#editpasswordParser
editPasswordParser =  reqparse.RequestParser()
editPasswordParser.add_argument('current_password', type=str, help='current_password',location='json', required=True)
editPasswordParser.add_argument('new_password', type=str, help='new_password',location='json', required=True)
@api.route('/editpassword')
class Password(Resource):
    @api.expect(authParser,editPasswordParser)
    def put(self):
        args = editPasswordParser.parse_args()
        argss = authParser.parse_args()
        bearerAuth  = argss['Authorization']
        cu_password = args['current_password']
        newpassword = args['new_password']
        try:
            jwtToken    = bearerAuth[7:]
            token = decodetoken(jwtToken)
            user = User.query.filter_by(id=token.get('user_id')).first()
            if check_password_hash(user.password, cu_password):
                user.password = generate_password_hash(newpassword)
                db.session.commit()
            else:
                return {'message' : 'Password Lama Salah'},400
        except:
            return {
                'message' : 'Token Tidak valid! Silahkan, Sign in!'
            }, 401
        return {'message' : 'Password Berhasil Diubah'}, 200
    


ALLOWED_EXTENSIONS = {'3gp', 'mkv', 'avi', 'mp4'}
def allowed_file(filename):
	return '.' in filename and \
		filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

detectParser = api.parser()
detectParser.add_argument('video', location='files', type=FileStorage, required=True)
#@api.route('/detect')
#class Detect(Resource):
#    @api.expect(detectParser)
#    def post(self):
#        args = detectParser.parse_args()
#        video = args['video']
#        if video and allowed_file(video.filename):
#            filename = secure_filename(video.filename)
#            video.save(os.path.join("./video", filename))
#            #subprocess.run(['python', 'detect.py', '--source', f'./video/{filename}', '--weights', 'best.pt', '--name', f'{filename}'])
#            #print('success predict')
#            os.remove(f'./video/{filename}')
#            print('success remove')
#            return send_file(os.path.join(f"./runs/detect/{filename}", filename), mimetype='video/mp4', as_attachment=True, download_name=filename)
#        else:
#            return {'message' : 'invalid file extension'},400

@api.route('/video')
class Detect(Resource):
    @api.expect(detectParser)
    def post(self):
        args = detectParser.parse_args()
        video = args['video']
        if video and allowed_file(video.filename):
            filename = secure_filename(video.filename)
            video.save(os.path.join("./video/", filename))
            subprocess.run(['python', 'detect.py', '--source', f'./video/{filename}', '--weights', 'best.pt','--conf', '0.3', '--name', f'{filename}'])
            os.remove(f'./video/{filename}')
            print('success remove')
            return send_file(os.path.join(f"./runs/detect/{filename}", filename), mimetype='video/mp4', as_attachment=True, download_name=filename)
        else:
            return {'message' : 'invalid file extension'},400

ALLOWED_EX = {'jpg', 'jpeg', 'png'}
def allowed_file(filename):
	return '.' in filename and \
		filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

detectParserr = api.parser()
detectParserr.add_argument('image', location='files', type=FileStorage, required=True)

@api.route('/image')
class Detect(Resource):
    @api.expect(detectParserr)
    def post(self):
        args = detectParserr.parse_args()
        image = args['image']
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join("./image/", filename))
            subprocess.run(['python', 'detect.py', '--source', f'./image/{filename}', '--weights', 'best.pt','--conf', '0.3', '--name', f'{filename}'])
            os.remove(f'./image/{filename}')
            print('success remove')
            return send_file(os.path.join(f"./runs/detect/{filename}", filename), mimetype='image/jpg', as_attachment=True, download_name=filename)
        else:
            return {'message' : 'invalid file extension'},400


@app.route("/realtime")
def hello_world():
    return render_template('index.html')

@app.route("/opencam", methods=['GET'])
def opencam():
    print("waittt opencammm")
    subprocess.run(['python', 'detect.py', '--source', '0', '--weights', 'best.pt','--conf', '0.3'])
    return "done"



if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import socketio


# toto mu hovorí kde ma začať 
app = Flask(__name__)


app.config['SECRET_KEY'] ='48ew456768gds6regvd564687'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sqlite.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)



from routes import *


# hosting python https://www.pythonanywhere.com/details/flask_hosting
# hosting pythonm https://www.youtube.com/watch?v=xTn4DXI8dyc
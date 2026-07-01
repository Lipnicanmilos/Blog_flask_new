from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from flask_ckeditor import CKEditor
from flask_socketio import SocketIO

from config import Config

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
mail = Mail(app)
ckeditor = CKEditor(app)
socketio = SocketIO(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
login_manager.login_message = 'Please log in ...'

# modely musia byť importované pred routes.py aj pred user_loaderom
from models import User


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


from routes import *  # noqa: E402,F401,F403 - registruje route handlery do 'app'


if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

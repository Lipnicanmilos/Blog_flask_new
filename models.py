from datetime import datetime
import flask_login
from werkzeug.security import check_password_hash, generate_password_hash
from app import db
from flask_login import UserMixin
from flask_wtf.file import FileField, FileAllowed
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
import app

class User(db.Model, UserMixin):
    id =  db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    image_file = db.Column(db.String(100), nullable=False, default='default.jpg')
    password = db.Column(db.String(100), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)
    comments = db.relationship('Comment', backref='user', passive_deletes=True)
    liked = db.relationship('PostLike', foreign_keys='PostLike.user_id', backref='user', lazy='dynamic')

    def like_post(self, post):
        if not self.has_liked_post(post):
            like = PostLike(user_id=self.id, post_id=post.id)
            db.session.add(like)

    def unlike_post(self, post):
        if self.has_liked_post(post):
            PostLike.query.filter_by(user_id=self.id, post_id=post.id).delete()

    def has_liked_post(self, post):
        return PostLike.query.filter(PostLike.user_id == self.id, PostLike.post_id == post.id).count() > 0

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"
    
    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}', '{self.id}')"
    
    def is_active(self):
        """True, as all users are active."""
        return True
    
    def get_id(self):
        """Return the email address to satisfy Flask-Login's requirements."""
        return self.id

    def is_authenticated(self):
        """Return True if the user is authenticated."""
        return True

    def is_anonymous(self):
        """False, as anonymous users aren't supported."""
        return False
    
    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


class Post(db.Model):
    id =  db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"), nullable=False)
    comments = db.relationship('Comment', backref='post', lazy=True)
    likes = db.relationship('PostLike', backref = 'post', lazy = 'dynamic')

    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}', '{self.user_id}')"

class Comment(db.Model):
    id =  db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    author = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id', ondelete="CASCADE"), nullable=False)

# ondelete="CASCADE" -- db.ForeignKey('post.id', ondelete="CASCADE") --zabezpečí vymazanie pri vymazaní usera

class PostLike(db.Model):
    __tablename__ = 'post_like'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))

posts = [
    {
        'autor': 'Meno Autora',
        'title': 'Nadpis',
        'content': 'Obsah',
        'date_posted': 'Máj 23, 2021'
    },
    {
        'autor': 'Meno Autora2',
        'title': 'Nadpis2',
        'content': 'Obsah2',
        'date_posted': 'jún 23, 2021'
    }
]

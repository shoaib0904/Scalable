from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from flask_bcrypt import generate_password_hash, check_password_hash
import secrets

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    session_token = db.Column(db.String(32), unique=True, nullable=True)
    sessions = db.relationship('Session', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_session_token(self):
        while True:
            token = secrets.token_hex(16)
            if not Session.query.filter_by(token=token).first():
                self.session_token = token
                break

    def revoke_session_token(self):
        self.session_token = None

class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String(32), nullable=True)

    def __repr__(self):
        return f'<Session {self.token}>'

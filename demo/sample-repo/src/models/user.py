import bcrypt
from src.database import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.Binary(60), nullable=False)

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    def check_password(self, password):
        return bcrypt.checkpw(password.encode(), self.password_hash)

    @classmethod
    def create(cls, data):
        user = cls(username=data["username"])
        user.set_password(data["password"])
        db.session.add(user)
        db.session.commit()
        return user

    def to_dict(self):
        return {"id": self.id, "username": self.username}

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Leaderboard(db.Model):
    __tablename__ = "leaderboard"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    player_name = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "player_name": self.player_name,
            "score": self.score,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }

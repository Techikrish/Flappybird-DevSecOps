from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os
import sys

app = Flask(__name__)
CORS(app)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "flappydb")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")

print(f"[DEBUG] Connecting to database: postgresql://{DB_USER}:***@{DB_HOST}:{DB_PORT}/{DB_NAME}", file=sys.stderr)

app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Score(db.Model):
    __tablename__ = "scores"
    id = db.Column(db.Integer, primary_key=True)
    player_name = db.Column(db.String(128), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, 
            "player_name": self.player_name, 
            "score": self.score, 
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/start", methods=["POST"])
def start_game():
    data = request.get_json() or {}
    name = data.get("name")
    if not name:
        return jsonify({"error": "name is required"}), 400
    return jsonify({"message": "started", "player_name": name}), 200

@app.route("/submit", methods=["POST"])
def submit_score():
    data = request.get_json() or {}
    name = data.get("name")
    score = data.get("score")
    if name is None or score is None:
        return jsonify({"error": "name and score required"}), 400
    try:
        s = Score(player_name=name, score=int(score))
        db.session.add(s)
        db.session.commit()
        print(f"[DEBUG] Score saved: {name} = {score}", file=sys.stderr)
        return jsonify({"message": "saved", "score": s.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Failed to save score: {str(e)}", file=sys.stderr)
        return jsonify({"error": str(e)}), 500

@app.route("/leaderboard", methods=["GET"])
def leaderboard():
    try:
        limit = int(request.args.get("limit", 10))
        rows = Score.query.order_by(Score.score.desc(), Score.created_at.asc()).limit(limit).all()
        print(f"[DEBUG] Leaderboard query returned {len(rows)} rows", file=sys.stderr)
        result = [r.to_dict() for r in rows]
        print(f"[DEBUG] Leaderboard result: {result}", file=sys.stderr)
        return jsonify(result), 200
    except Exception as e:
        print(f"[ERROR] Leaderboard error: {str(e)}", file=sys.stderr)
        return jsonify({"error": str(e)}), 500

@app.route("/seed", methods=["POST"])
def seed_data():
    """Seed some test data for debugging"""
    try:
        # Clear existing data
        Score.query.delete()
        db.session.commit()
        
        # Add test data
        test_scores = [
            Score(player_name="Alice", score=150),
            Score(player_name="Bob", score=120),
            Score(player_name="Charlie", score=100),
        ]
        for s in test_scores:
            db.session.add(s)
        db.session.commit()
        
        print("[DEBUG] Test data seeded", file=sys.stderr)
        return jsonify({"message": "seeded", "count": len(test_scores)}), 201
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Seed error: {str(e)}", file=sys.stderr)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("[DEBUG] Starting Flask app", file=sys.stderr)
    with app.app_context():
        print("[DEBUG] Creating database tables", file=sys.stderr)
        db.create_all()
        print("[DEBUG] Database tables created", file=sys.stderr)
    print("[DEBUG] Running Flask server", file=sys.stderr)
    app.run(host="0.0.0.0", port=5000, debug=True)

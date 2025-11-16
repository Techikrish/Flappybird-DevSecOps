from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Score

app = Flask(__name__)
CORS(app)

DATABASE_URL = "sqlite:///scores.db"

# SQLAlchemy engine + session
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

# Create tables ONCE at startup (safe)
try:
    Base.metadata.create_all(bind=engine)
    print("✔ Tables created")
except Exception as e:
    print("⚠ Failed to create tables:", e)


@app.post("/score")
def submit_score():
    data = request.get_json()
    player_name = data.get("player_name")
    score_value = data.get("score")

    if not player_name or score_value is None:
        return jsonify({"error": "player_name and score required"}), 400

    session = SessionLocal()
    try:
        new_score = Score(username=player_name, score=score_value)
        session.add(new_score)
        session.commit()
        return jsonify({"message": "Score saved"})
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@app.get("/scores")
def leaderboard():
    session = SessionLocal()
    try:
        scores = session.query(Score).order_by(Score.score.desc()).limit(10).all()

        # Convert SQLAlchemy objects → JSON dictionary
        leaderboard_data = [
            {
                "player_name": s.username,
                "score": s.score
            }
            for s in scores
        ]

        return jsonify(leaderboard_data)

    finally:
        session.close()


@app.get("/")
def home():
    return "Backend running"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

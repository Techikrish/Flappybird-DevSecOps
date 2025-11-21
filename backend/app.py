import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Score

app = Flask(__name__)
CORS(app)

# -------------------------------------------------------------------
# Database config from environment variables (Helm will provide them)
# -------------------------------------------------------------------
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

if not DB_HOST or not DB_NAME or not DB_USER or not DB_PASS:
    raise RuntimeError("❌ Missing one or more DB environment variables")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:5432/{DB_NAME}"

# -------------------------------------------------------------------
# SQLAlchemy engine and session
# -------------------------------------------------------------------
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# -------------------------------------------------------------------
# Create DB tables only once at startup
# -------------------------------------------------------------------
try:
    Base.metadata.create_all(bind=engine)
    print("✔ PostgreSQL tables created")
except Exception as e:
    print("⚠ Failed to create tables:", e)

# -------------------------------------------------------------------
# Routes
# -------------------------------------------------------------------
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
        scores = (
            session.query(Score)
            .order_by(Score.score.desc())
            .limit(10)
            .all()
        )

        leaderboard_data = [
            {
                "player_name": s.username,
                "score": s.score
            } for s in scores
        ]

        return jsonify(leaderboard_data)
    finally:
        session.close()


@app.get("/")
def home():
    return "Backend running (PostgreSQL mode)"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
from prometheus_client import make_wsgi_app, Counter, Histogram, Gauge
from werkzeug.middleware.dispatcher import DispatcherMiddleware
import os
import sys
import time

app = Flask(__name__)
CORS(app)

# -----------------------------
# Prometheus metrics
# -----------------------------
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

active_connections = Gauge(
    'active_connections',
    'Number of active connections'
)

scores_submitted_total = Counter(
    'scores_submitted_total',
    'Total scores submitted',
    ['player_name']
)

# Metrics endpoint
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    '/metrics': make_wsgi_app()
})

# -----------------------------
# Database Configuration
# -----------------------------
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "flappydb")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")

# ❗ Ensure DB_HOST does NOT include a port accidentally
if ":" in DB_HOST:
    print("[ERROR] Your DB_HOST contains a port! It must ONLY be the hostname.", file=sys.stderr)
    print(f"[ERROR] DB_HOST provided = {DB_HOST}", file=sys.stderr)
    # Extract hostname before first ':'
    DB_HOST = DB_HOST.split(":")[0]
    print(f"[FIX] Using sanitized DB_HOST = {DB_HOST}", file=sys.stderr)

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

print(f"[DEBUG] Final DATABASE_URL = {DATABASE_URL.replace(DB_PASS, '***')}", file=sys.stderr)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# -----------------------------
# Database Model
# -----------------------------
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

# -----------------------------
# Middleware
# -----------------------------
@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    duration = time.time() - request.start_time
    http_request_duration_seconds.labels(
        method=request.method,
        endpoint=request.endpoint or 'unknown'
    ).observe(duration)
    http_requests_total.labels(
        method=request.method,
        endpoint=request.endpoint or 'unknown',
        status=response.status_code
    ).inc()
    return response

# -----------------------------
# Endpoints
# -----------------------------
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
        scores_submitted_total.labels(player_name=name).inc()
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
        print(f"[DEBUG] Leaderboard returned {len(rows)} rows", file=sys.stderr)
        return jsonify([r.to_dict() for r in rows]), 200
    except Exception as e:
        print(f"[ERROR] Leaderboard error: {str(e)}", file=sys.stderr)
        return jsonify({"error": str(e)}), 500

@app.route("/seed", methods=["POST"])
def seed_data():
    """Manually seed the DB for debugging"""
    try:
        Score.query.delete()
        db.session.commit()

        test_scores = [
            Score(player_name="Alice", score=150),
            Score(player_name="Bob", score=120),
            Score(player_name="Charlie", score=100),
        ]
        db.session.add_all(test_scores)
        db.session.commit()

        print("[DEBUG] Seed data inserted", file=sys.stderr)
        return jsonify({"message": "seeded", "count": len(test_scores)}), 201
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Seed error: {str(e)}", file=sys.stderr)
        return jsonify({"error": str(e)}), 500

# -----------------------------
# App Start
# -----------------------------
if __name__ == "__main__":
    print("[DEBUG] Starting Flask app", file=sys.stderr)
    with app.app_context():
        print("[DEBUG] Creating tables if not exist", file=sys.stderr)
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)

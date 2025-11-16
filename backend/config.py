import os
from urllib.parse import urlparse

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://flappy:flappy_pass@db:5432/flappydb")
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))

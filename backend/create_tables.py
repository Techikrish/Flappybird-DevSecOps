import time
from sqlalchemy.exc import OperationalError
from app import engine
from models import Base

MAX_RETRIES = 20
DELAY = 3  # seconds

for attempt in range(MAX_RETRIES):
    try:
        Base.metadata.create_all(bind=engine)
        print("✔ Tables created successfully.")
        break
    except OperationalError as e:
        print(f"DB not ready ({attempt+1}/{MAX_RETRIES}): {e}")
        time.sleep(DELAY)
    except Exception as e:
        print(f"Unexpected error: {e}")
        time.sleep(DELAY)
else:
    print("❌ ERROR: Database unavailable after maximum retries.")

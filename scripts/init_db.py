import sys
import time
from sqlalchemy import create_engine, text
from app.core.config.settings import settings
from app.core.database.session import Base
from app.models.manager import Manager
from app.models.call import Call
from app.models.transcript import Transcript
from app.models.ai_analysis import AIAnalysis
from app.models.processing_job import ProcessingJob
from app.models.processing_log import ProcessingLog

def init_db():
    print("Connecting to Database at", settings.SYNC_DATABASE_URL)
    engine = create_engine(settings.SYNC_DATABASE_URL)

    retries = 10
    connected = False
    while retries > 0:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                connected = True
                break
        except Exception as e:
            print("Database not ready yet, retrying...", str(e))
            retries -= 1
            time.sleep(2)

    if not connected:
        print("Could not connect to Database. Exiting.")
        sys.exit(1)

    import os
    reset_db = os.getenv("RESET_DB", "false").lower() == "true"
    if reset_db:
        print("RESET_DB is set to true. Dropping all existing database tables...")
        Base.metadata.drop_all(bind=engine)
        print("Database tables dropped successfully!")

    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_db()

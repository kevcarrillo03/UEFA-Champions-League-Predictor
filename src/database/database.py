from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.models import Base

import os
database_url = os.getenv("DATABASE_URL", "postgresql://ucl_user:ucl_password@localhost:5432/ucl_predictor")

engine = create_engine(database_url, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_table():
    print("creating database tables")
    Base.metadata.create_all(bind=engine)
    print("tabels created")

if __name__ == "__main__":
    create_table()
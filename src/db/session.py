from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.utilities.paths import get_database_file_path

DATABASE_URL = f"sqlite:///{get_database_file_path()}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

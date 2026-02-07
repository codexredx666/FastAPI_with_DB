from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
load_dotenv()

Base=declarative_base() 

DATABASE_URL=os.getenv("DATABASE_URL")
print("DATABASE_URL",DATABASE_URL)
#create engine once at module level
engine=create_engine(DATABASE_URL)

#create sessionaLocal class for creatimg database sessions
SessionLocal=sessionmaker(autocommit=False, autoflush=False, bind=engine)
def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()
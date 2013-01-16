from pecan import conf

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from model import Base

engine = None
session_maker = None

def init_model():
    engine = create_engine('sqlite:///:memory:', echo=True)
    Base.metadata.create_all(engine)
    session_maker = sessionmaker(bind=engine)

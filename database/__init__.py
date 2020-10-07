from sqlalchemy.orm import sessionmaker, scoped_session
from . import models

Session = sessionmaker(bind=models.engine)
session = scoped_session(Session)
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///mail_tasks.db')
Session = sessionmaker(bind=engine)
session = Session()

session.execute(text("DELETE FROM tasks"))
session.execute(text("DELETE FROM users"))
session.execute(text("DELETE FROM gmail_credentials"))

session.commit()

session.close() 

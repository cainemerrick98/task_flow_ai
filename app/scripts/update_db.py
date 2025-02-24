from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///mail_tasks.db')
Session = sessionmaker(bind=engine)
session = Session()

session.execute(text("UPDATE users SET is_google_authenticated = 1"))

session.commit()

result = session.execute(text("SELECT * FROM users"))

print(result.fetchall())

session.close()

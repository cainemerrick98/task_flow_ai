"""
this scripts deletes the database file and creates a new one
"""

import os
from app.models import create_database

if os.path.exists('mail_tasks.db'):
    os.remove('mail_tasks.db')

create_database()

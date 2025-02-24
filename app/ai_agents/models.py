from pydantic import BaseModel
from datetime import date
from typing import Optional

class Task(BaseModel):
    title: str
    due_date: Optional[date] = None
    description: str

    def __str__(self):
        return f"Task: {self.task}\nDue Date: {self.due_date}\nDescription: {self.description}"

    def __repr__(self):
        return self.__str__()



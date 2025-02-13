from pydantic import BaseModel

class Task(BaseModel):
    task: str
    due_date: str | None
    description: str

    def __str__(self):
        return f"Task: {self.task}\nDue Date: {self.due_date}\nDescription: {self.description}"

    def __repr__(self):
        return self.__str__()



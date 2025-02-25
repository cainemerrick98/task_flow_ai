import logging
from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from app.models import Task, User, get_db
from app.ai_agents.models import Task as TaskModel


router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/tasks", response_model=list[TaskModel])
async def get_tasks(user_id: int = Header(description="The ID of the user"), db: Session = Depends(get_db)):
    """Get all tasks for the current user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    tasks = db.query(Task).filter(Task.user_id == user_id).all()
    return tasks

@router.put("/tasks/{task_id}", response_model=TaskModel)
async def update_task(task_id: int, task: TaskModel, db: Session = Depends(get_db)):
    """Update a task"""
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    db_task.title = task.title
    db_task.description = task.description
    db_task.due_date = task.due_date
    db.commit()
    db.refresh(db_task)
    return db_task



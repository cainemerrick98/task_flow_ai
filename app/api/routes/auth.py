from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import logging
from app.models import User, get_db

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post('/login')
async def login(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    email = data.get('email')
    password = data.get('password') 
    print(f"email: {email}, password: {password}")
    print(f"db type: {type(db)}")
    print(f"db query type: {type(db.query)}")
    user = db.query(User).filter(User.email == email).first()
    print(f"user: {user}")
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.password == password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return JSONResponse(
        status_code=200,
        content={
            "message": "Successfully logged in", 
            "user": {
                "id": user.id, 
                "email": user.email
            }
        }
    )


@router.post('/register')
async def register(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    email = data.get('email')
    password = data.get('password')
    user = User(email=email, password=password)
    db.add(user)
    db.commit()
    return JSONResponse(status_code=200, content={"message": "Successfully registered"})


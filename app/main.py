from fastapi import FastAPI
from fastapi.responses import RedirectResponse
import logging
import uvicorn

from app.api.routes import auth, integrations, tasks
from app.services.gmail_polling import start_polling_thread
from app.models import create_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

app = FastAPI()

# Include routers
app.include_router(auth.router, tags=["auth"])
app.include_router(integrations.google_router, tags=["integrations"])
app.include_router(tasks.router, tags=["tasks"])

if __name__ == "__main__":
    # Create database
    create_database()
    
    # Start the polling thread
    polling_thread = start_polling_thread()
    
    # Start the FastAPI app
    uvicorn.run('app.main:app', host="127.0.0.1", port=8000, reload=False) 
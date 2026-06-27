from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import uvicorn
import json
import os
from dotenv import load_dotenv

# Import our custom modules
from api.routes import router as api_router
from api.v1 import router as v1_router
from api.admin import router as admin_router
from api.keys import router as keys_router
from config import settings

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="SearchGPT Agent API",
    description="Backend API for the SearchE Agent web research tool",
    version="1.0.0"
)

# Add CORS middleware to allow requests from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with actual frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)
app.include_router(v1_router)     # Public Data API v1 (Problem 4)
app.include_router(admin_router)  # Admin analytics dashboard API (Problem 5)
app.include_router(keys_router)   # API key management (Developers)

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the SearchE Agent API"}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True) 
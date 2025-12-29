"""
AudioAI Backend - Main FastAPI Application
Audio preprocessing platformasi uchun asosiy backend server
"""

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
import shutil
from pathlib import Path
from typing import Optional
import logging

# Local imports
from api.routes import router
from utils.audio_utils import create_directories

# Logging sozlamalari
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI ilovasi yaratish
app = FastAPI(
    title="AudioAI API",
    description="Professional Audio Preprocessing Platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS sozlamalari (Frontend bilan bog'lanish uchun)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production'da aniq domenlarni ko'rsating
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Kerakli papkalarni yaratish
@app.on_event("startup")
async def startup_event():
    """Server ishga tushganda kerakli papkalarni yaratadi"""
    try:
        create_directories()
        logger.info("✅ Barcha kerakli papkalar yaratildi")
    except Exception as e:
        logger.error(f"❌ Papkalar yaratishda xato: {e}")

# API routes'larini ulash
app.include_router(router, prefix="/api/v1")

# Health check endpoint
@app.get("/")
async def root():
    """API ishlayotganini tekshirish"""
    return {
        "status": "online",
        "service": "AudioAI API",
        "version": "1.0.0",
        "message": "Audio preprocessing API ishga tushdi!"
    }

@app.get("/health")
async def health_check():
    """Server health status"""
    return {
        "status": "healthy",
        "uptime": "running"
    }

# Server ishga tushirish
if __name__ == "__main__":
    logger.info("🚀 AudioAI Backend ishga tushmoqda...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Development mode uchun
        log_level="info"
    )

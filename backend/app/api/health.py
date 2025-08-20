from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import os
import platform
import sys
from datetime import datetime

router = APIRouter()

@router.get("/", response_model=Dict[str, Any])
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "environment": os.environ.get("ENVIRONMENT", "development")
    }

@router.get("/system", response_model=Dict[str, Any])
async def system_info():
    """System information endpoint"""
    return {
        "python_version": sys.version,
        "platform": platform.platform(),
        "memory": {
            "available": "N/A"  # Would implement actual memory monitoring in production
        },
        "cpu": {
            "usage": "N/A"  # Would implement actual CPU monitoring in production
        }
    }

@router.get("/ping")
async def ping():
    """Simple ping endpoint for load balancers"""
    return {"ping": "pong"}

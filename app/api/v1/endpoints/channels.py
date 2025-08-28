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
from app.db.session import get_db
from app.schemas.channel import Channel, ChannelBase
from app.db.repositories.channel import get_channels, get_channel, create_channel
from app.core.security import get_current_active_user
from app.schemas.user import User

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
active_streams = {}

def get_channel_by_name(channel_name: str):
    """
    Helper function to get a channel from the static list by name.
    """
    for channel in static_channels:
        if channel["re_stream_id"] == channel_name:
            return channel
    return None

def stop_ffmpeg_process(stream_id: str):
    """
    Stops the FFmpeg process for a given stream.
    """
    if stream_id in active_streams:
        process = active_streams.pop(stream_id)
        process.terminate()
        print(f"Stopped FFmpeg process for '{stream_id}'.")

async def run_ffmpeg_process(stream_id: str, source_url: str):
    """
    Runs an FFmpeg command in a subprocess to re-stream the content.
    """
    # Check if the stream is already running
    if stream_id in active_streams and active_streams[stream_id].poll() is None:
        return

    output_dir = os.path.join(HLS_OUTPUT_DIR, stream_id)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # The FFmpeg command to re-stream and save to the output directory
    command = [
        'ffmpeg',
        '-i', source_url,  # Input stream URL
        '-c:v', 'copy',      # Copy video codec without re-encoding
        '-c:a', 'copy',      # Copy audio codec without re-encoding
        '-hls_time', '2',  # Duration of each HLS segment
        '-hls_list_size', '5',  # Number of segments in the playlist
        '-f', 'hls',         # Output format is HLS
        os.path.join(output_dir, 'master.m3u8')  # Output M3U8 file path
    ]

    try:
        # Start the FFmpeg process
        print(f"Starting FFmpeg process for '{stream_id}'...")
        process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        active_streams[stream_id] = process
        
    except FileNotFoundError:
        print("FFmpeg not found. Please ensure it is installed and in your system's PATH.")
    except Exception as e:
        print(f"An error occurred while starting the FFmpeg process for '{stream_id}': {e}")


@router.get("/hls/{channel_name}/master.m3u8")
async def get_hls_stream(channel_name: str, background_tasks: BackgroundTasks):
    """
    Starts FFmpeg process for the requested channel and then serves the HLS master playlist file.
    This endpoint now handles both starting the stream and serving the master.m3u8 file.
    """
    channel = get_channel_by_name(channel_name)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
        
    stream_id = channel["re_stream_id"]
    source_url = channel["url"]

    # Start the FFmpeg process in the background
    background_tasks.add_task(run_ffmpeg_process, stream_id, source_url)

    # Wait for a brief moment to allow FFmpeg to start and create files
    # This is to prevent a race condition where the player requests the file before it exists.
    await asyncio.sleep(2)

    # Now, try to serve the file from the correct static directory
    file_path = os.path.join(HLS_OUTPUT_DIR, stream_id, "master.m3u8")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="HLS stream not available yet. Please try again in a few seconds.")

    with open(file_path, "rb") as f:
        content = f.read()

    return Response(content=content, media_type="application/vnd.apple.mpegurl")

@router.get("/static-hls-m3u")
async def get_static_hls_playlist(background_tasks: BackgroundTasks):
    """
    Generates an M3U playlist with HLS links pointing to the re-streamed content on this server.
    """
    m3u_content = "#EXTM3U\n"
    
    server_base_url = "http://5.63.19.76:8000"

    for channel in static_channels:
        # Ensure the FFmpeg process is started for each channel
        # This is a better place to start the stream than the main API.
        background_tasks.add_task(run_ffmpeg_process, channel["re_stream_id"], channel["url"])
        
        # Create the new HLS link that points to your server's mounted HLS folder
        hls_url = f"{server_base_url}/hls_streams/{quote(channel['re_stream_id'])}/master.m3u8"
        
        m3u_content += f'#EXTINF:-1 tvg-name=\"{channel["name"]}\" tvg-logo=\"{channel["logo"]}\" group-title=\"{channel["group"]}\",{channel["name"]}\n'
        m3u_content += f'{hls_url}\n'

    # Return the playlist with the correct media type for players
    return Response(content=m3u_content, media_type="audio/x-mpegurl")

# Existing endpoint to get channels from the database
@router.get("/", response_model=List[Channel])
def read_channels(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieves a list of channels from the database, requiring an authenticated user.
    """
    channels = get_channels(db, skip=skip, limit=limit)
    return channels

# Existing endpoint to generate an M3U playlist from the database
@router.get("/m3u")
def get_m3u_playlist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Generates a dynamic M3U playlist based on channels in the database and user subscription.
    """
    channels = get_channels(db)
    m3u_content = "#EXTM3U\n"
    for channel in channels:
        if channel.is_premium and current_user.subscription_plan == "free":
            continue
        m3u_content += f'#EXTINF:-1 tvg-id=\"{channel.id}\" tvg-name=\"{channel.name}\" tvg-logo=\"{channel.logo}\" group-title=\"{channel.m3u_group}\",{channel.name}\n'
        m3u_content += f"{channel.url}\n"
    return Response(content=m3u_content, media_type="audio/x-mpegurl")

# New endpoint to generate a static M3U playlist
@router.get("/static-m3u")
def get_static_m3u_playlist():
    """
    Generates a static M3U playlist from a predefined list of links.
    This endpoint does not require authentication.
    """
    m3u_content = "#EXTM3U\n"
    for channel in static_channels:
        m3u_content += f'#EXTINF:-1 tvg-name=\"{channel["name"]}\" tvg-logo=\"{channel["logo"]}\" group-title=\"{channel["group"]}\",{channel["name"]}\n'
        m3u_content += f'{channel["url"]}\n'
    return Response(content=m3u_content, media_type="audio/x-mpegurl")

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.schemas.channel import Channel, ChannelBase
from app.db.repositories.channel import get_channels, get_channel, create_channel
from app.core.security import get_current_active_user
from app.schemas.user import User

router = APIRouter()

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
        m3u_content += f'#EXTINF:-1 tvg-id="{channel.id}" tvg-name="{channel.name}" tvg-logo="{channel.logo}" group-title="{channel.m3u_group}",{channel.name}\n'
        m3u_content += f"{channel.url}\n"
    return Response(content=m3u_content, media_type="audio/x-mpegurl")

# New endpoint to generate a static M3U playlist
@router.get("/static-m3u")
def get_static_m3u_playlist():
    """
    Generates a static M3U playlist from a predefined list of links.
    This endpoint does not require authentication.
    """
    # A list of static channels. You can add more channels to this list.
    static_channels = [
        {
            "name": "4tv News",
            "url": "http://51.254.122.232:5005/stream/tata/4tvnews/master.m3u8?u=atech&p=1491fed6b7de88547a8fd33cdb98e457a54e142527b1b59f6c0502a8a87fb6bb",
            "logo": "https://99designs-blog.imgix.net/blog/wp-content/uploads/2022/06/attachment_135299869.jpeg",
            "group": "News"
        },
        {
            "name": "7x Music",
            "url": "http://51.254.122.232:5005/stream/tata/7xmusic/master.m3u8?u=atech&p=1491fed6b7de88547a8fd33cdb98e457a54e142527b1b59f6c0502a8a87fb6bb",
            "logo": "https://99designs-blog.imgix.net/blog/wp-content/uploads/2022/06/attachment_135299869.jpeg",
            "group": "News"
        },
        {
            "name": "9X Jalwa",
            "url": "http://51.254.122.232:5005/stream/tata/9xjalwa/master.m3u8?u=atech&p=1491fed6b7de88547a8fd33cdb98e457a54e142527b1b59f6c0502a8a87fb6bb",
            "logo": "https://99designs-blog.imgix.net/blog/wp-content/uploads/2022/06/attachment_135299869.jpeg",
            "group": "News"
        },
        {
            "name": "AB STAR News",
            "url": "http://51.254.122.232:5005/stream/tata/abstarnews/master.m3u8?u=atech&p=1491fed6b7de88547a8fd33cdb98e457a54e142527b1b59f6c0502a8a87fb6bb",
            "logo": "https://99designs-blog.imgix.net/blog/wp-content/uploads/2022/06/attachment_135299869.jpeg",
            "group": "News"
        },
        {
            "name": "ABC News",
            "url": "http://51.254.122.232:5005/stream/tata/abcnews/master.m3u8?u=atech&p=1491fed6b7de88547a8fd33cdb98e457a54e142527b1b59f6c0502a8a87fb6bb",
            "logo": "https://99designs-blog.imgix.net/blog/wp-content/uploads/2022/06/attachment_135299869.jpeg",
            "group": "News"
        },
        {
            "name": "ABP Asmita",
            "url": "http://51.254.122.232:5005/stream/tata/abpasmita/master.m3u8?u=atech&p=1491fed6b7de88547a8fd33cdb98e457a54e142527b1b59f6c0502a8a87fb6bb",
            "logo": "https://99designs-blog.imgix.net/blog/wp-content/uploads/2022/06/attachment_135299869.jpeg",
            "group": "News"
        },
        {
            "name": "Action Cinema",
            "url": "http://51.254.122.232:5005/stream/tata/actioncinema/master.m3u8?u=atech&p=1491fed6b7de88547a8fd33cdb98e457a54e142527b1b59f6c0502a8a87fb6bb",
            "logo": "https://99designs-blog.imgix.net/blog/wp-content/uploads/2022/06/attachment_135299869.jpeg",
            "group": "News"
        },
        {
            "name": "Al Jazeera",
            "url": "http://51.254.122.232:5005/stream/tata/aljazeera/master.m3u8?u=atech&p=1491fed6b7de88547a8fd33cdb98e457a54e142527b1b59f6c0502a8a87fb6bb",
            "logo": "https://99designs-blog.imgix.net/blog/wp-content/uploads/2022/06/attachment_135299869.jpeg",
            "group": "News"
        },
        {
            "name": "ANN News",
            "url": "http://51.254.122.232:5005/stream/tata/annnews/master.m3u8?u=atech&p=1491fed6b7de88547a8fd33cdb98e457a54e142527b1b59f6c0502a8a87fb6bb",
            "logo": "https://99designs-blog.imgix.net/blog/wp-content/uploads/2022/06/attachment_135299869.jpeg",
            "group": "News"
        }
    ]

    m3u_content = "#EXTM3U\n"
    for channel in static_channels:
        m3u_content += f'#EXTINF:-1 tvg-name="{channel["name"]}" tvg-logo="{channel["logo"]}" group-title="{channel["group"]}",{channel["name"]}\n'
        m3u_content += f'{channel["url"]}\n'

    # Return the playlist with the correct media type for players
    return Response(content=m3u_content, media_type="audio/x-mpegurl")
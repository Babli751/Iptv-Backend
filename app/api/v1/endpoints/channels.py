from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.schemas.channel import Channel, ChannelBase
from app.db.repositories.channel import get_channels, get_channel, create_channel
from app.core.security import get_current_active_user
from app.schemas.user import User

router = APIRouter()

@router.get("/", response_model=List[Channel])
def read_channels(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    channels = get_channels(db, skip=skip, limit=limit)
    return channels

@router.get("/m3u")
def get_m3u_playlist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    channels = get_channels(db)
    m3u_content = "#EXTM3U\n"
    for channel in channels:
        if channel.is_premium and current_user.subscription_plan == "free":
            continue
        m3u_content += f'#EXTINF:-1 tvg-id="{channel.id}" tvg-name="{channel.name}" tvg-logo="{channel.logo}" group-title="{channel.m3u_group}",{channel.name}\n'
        m3u_content += f"{channel.url}\n"
    return {"content": m3u_content}
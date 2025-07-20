from sqlalchemy.orm import Session
from typing import List
from app.models.channel import Channel
from app.schemas.channel import ChannelBase

def get_channels(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Channel).offset(skip).limit(limit).all()

def get_channel(db: Session, channel_id: int):
    return db.query(Channel).filter(Channel.id == channel_id).first()

def create_channel(db: Session, channel: ChannelBase):
    db_channel = Channel(**channel.dict())
    db.add(db_channel)
    db.commit()
    db.refresh(db_channel)
    return db_channel
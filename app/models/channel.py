from sqlalchemy import Boolean, Column, Integer, String, Text  # Gerekli tipleri import edin
from app.db.base import Base

class Channel(Base):
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    url = Column(String)
    category = Column(String)
    language = Column(String)
    logo = Column(String)
    is_premium = Column(Boolean, default=False)
    m3u_group = Column(String)
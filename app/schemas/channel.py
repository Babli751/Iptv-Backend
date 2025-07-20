from pydantic import BaseModel

class ChannelBase(BaseModel):
    name: str
    url: str
    category: str = None
    language: str = None
    logo: str = None
    is_premium: bool = False
    m3u_group: str = None

class Channel(ChannelBase):
    id: int

    class Config:
        orm_mode = True
from datetime import date
from sqlalchemy import Date, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base

class SocialMediaPost(Base):
    __tablename__ = "social_media_posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_id: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    platform: Mapped[str] = mapped_column(String(30), index=True)
    content_type: Mapped[str] = mapped_column(String(30), index=True)
    caption: Mapped[str] = mapped_column(String(1000), default="")
    hashtags: Mapped[str] = mapped_column(String(500), default="")
    reach: Mapped[int] = mapped_column(Integer, default=0)
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    likes: Mapped[int] = mapped_column(Integer, default=0)
    comments: Mapped[int] = mapped_column(Integer, default=0)
    shares: Mapped[int] = mapped_column(Integer, default=0)
    followers_start: Mapped[int] = mapped_column(Integer, default=0)
    new_followers: Mapped[int] = mapped_column(Integer, default=0)
    lost_followers: Mapped[int] = mapped_column(Integer, default=0)
    sentiment: Mapped[str] = mapped_column(String(20), default="neutral")
    posted_hour: Mapped[int] = mapped_column(Integer, default=12)

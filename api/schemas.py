
from enum import Enum
from uuid import UUID
from pydantic import BaseModel, field_serializer, HttpUrl
from typing import Optional
import datetime

class SubscriptionType(str, Enum):
    FREE = "FREE"
    PRO = "PRO"
    PREMIUM = "PREMIUM"


class LoginRequest(BaseModel):
    email: str
    password: str
    remember: bool

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    

class UserCreateRequest(BaseModel):
    username: str
    email: str
    password: str
    confirm_password: str
    bio: Optional[str] = ""
    photo_url: Optional[str] = None

    class Config:
        from_attributes = True

class UserCreateResponse(BaseModel):
    uuid: UUID

    class Config:
        from_attributes = True


class UserProfile(BaseModel):
    uuid: UUID
    username: str
    email: str
    bio: Optional[str] = ""
    photo_url: Optional[str] = ""
    
    @field_serializer('photo_url')
    def format_photo_url(self, photo_url: str) -> HttpUrl:
        if not photo_url:
            photo_url = HttpUrl(
                "https://ui-avatars.com/api/?name={username}&background=random".format(
                    username=self.username
                    )
                )
        return photo_url
    
    class Config:
        from_attributes = True


class TagCreateRequest(BaseModel):
    name: str
    group: str
    color: str

class Tag(BaseModel):
    uuid: UUID
    name: str
    group: str
    color: str

    class Config:
        from_attributes = True

class PostCreateRequest(BaseModel):
    title: str
    content: str
    categories: list[str]


class Post(BaseModel):
    uuid: UUID
    title: str
    content: str
    categories: list[Tag]

    class Config:
        from_attributes = True

class TagPreview(BaseModel):
    name: str
    color: str

    class Config:
        from_attributes = True

class ReactionCountPreview(BaseModel):
    love: int
    like: int
    support: int
    sad: int
    user_reaction: Optional[str]

    class Config:
        from_attributes = True

class PostPreview(BaseModel):
    uuid: UUID
    title: str
    content: str
    username: str
    created_at: datetime.datetime
    is_bookmarked: bool
    tags: list[TagPreview]
    reactions: ReactionCountPreview

    @field_serializer('content')
    def truncate_content(self, content: str) -> str:
        return content[:240] + '...' if len(content) > 240 else content

    @field_serializer('created_at')
    def format_created_at(self, created_at: str) -> str:    
        return created_at.strftime('%Y-%m-%d %H:%M:%S')
    class Config:
        from_attributes = True


class ReactionRequest(BaseModel):
    post_uuid: str
    reaction: str


class ReactionCount(BaseModel):
    love: int
    like: int
    support: int
    sad: int

class ReactionResponse(BaseModel):
    status: str
    message: str
    reaction: str
    counts: ReactionCount


class PostDetail(BaseModel):
    uuid: UUID
    title: str
    content: str
    username: str
    created_at: datetime.datetime
    is_bookmarked: bool
    tags: list[TagPreview]
    reactions: ReactionCountPreview



class UserPreview(BaseModel):
    uuid: UUID
    username: str
    bio: Optional[str]
    photo_url: Optional[str] = None
    last_post_date: Optional[datetime.datetime]
    top_tags: Optional[list[TagPreview]]
    
    @field_serializer('photo_url')
    def format_photo_url(self, photo_url: str) -> HttpUrl:
        if not photo_url:
            photo_url = HttpUrl(
                "https://ui-avatars.com/api/?name={username}&background=random".format(
                    username=self.username
                    )
                )
        return photo_url
    
    @field_serializer('last_post_date')
    def format_last_post_date(self, last_post_date: str) -> str:
        if last_post_date: return last_post_date.strftime('%Y-%m-%d %H:%M:%S') 
        return last_post_date
    class Config:
        from_attributes = True


class UserProfileVisit(BaseModel):
    username: str
    bio: str
    photo_url: Optional[str] = ""
    created_at: datetime.datetime
    total_reactions: dict
    is_following: bool
    posts_preview: list[PostPreview]
    total_posts: int


    @field_serializer('created_at')
    def format_created_at(self, created_at: str) -> str:    
        return created_at.strftime('%Y-%m-%d')
    
    @field_serializer('photo_url')
    def format_photo_url(self, photo_url: str) -> HttpUrl:
        if not photo_url:
            photo_url = HttpUrl(
                "https://ui-avatars.com/api/?name={username}&background=random".format(
                    username=self.username
                    )
                )
        return photo_url


class NotificationCreateRequest(BaseModel):
    title: str
    content: str
    notification_type: str
    user_generator: UUID
    user_receiver: UUID
    post_id: UUID

class NotificationResponse(BaseModel):
    uuid: UUID
    post_id: UUID
    title: str
    message: str
    read: bool
    notification_type: str
    created_at: datetime.datetime

    @field_serializer('created_at')
    def format_created_at(self, created_at: str) -> str:    
        return created_at.strftime('%Y-%m-%d %H:%M')
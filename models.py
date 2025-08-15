from datetime import datetime, timezone
from enum import Enum
import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Text, Table, func, Enum as SqlEnum  
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base



class SubscriptionType(Enum):
    FREE = 0
    PRO = 1
    PREMIUM = 2

class ReactionType(Enum):
    LIKE = "like"
    LOVE = "love"
    SUPPORT = "support"
    SAD = "sad"

class NotificationType(Enum):
    ATT = "att"
    NEW = "new"



class User(Base):
    __tablename__ = 'users'

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    password = Column(String(100), nullable=False)
    bio = Column(String(255), nullable=True)
    photo_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    subscriptions = relationship("UserSubscription", back_populates="user")
    posts = relationship("Post", back_populates="user")
    bookmarks = relationship("PostBookmark", back_populates="user")

    def __repr__(self):
        return f"<User {self.username}>"

class UserSubscription(Base):
    __tablename__ = 'user_subscriptions'

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.uuid'))
    status = Column(Boolean, default=True)
    subscription = Column(Integer, default=SubscriptionType.FREE.value)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="subscriptions")

    def __repr__(self):
        return f"<UserSubscription {self.subscription}>"

class Tag(Base):
    __tablename__ = 'tags'

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    active = Column(Boolean, default=True)
    group = Column(String(100), nullable=False)
    color = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    posts = relationship("Post", secondary="post_tags", back_populates="tags")

    def __repr__(self):
        return f"<Tag {self.name}>"


class Post(Base):
    __tablename__ = 'posts'

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.uuid'))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="posts")
    tags = relationship("Tag", secondary="post_tags", back_populates="posts")
    bookmarks = relationship("PostBookmark", back_populates="post")

class PostReaction(Base):
    __tablename__ = "post_reactions"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.uuid"), primary_key=True)
    post_id = Column(UUID(as_uuid=True), ForeignKey("posts.uuid"), primary_key=True)
    reaction_type = Column(SqlEnum(ReactionType), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

class PostReactionCount(Base):
    __tablename__ = "post_reaction_counts"
    post_id = Column(UUID(as_uuid=True), ForeignKey("posts.uuid"), primary_key=True)
    love = Column(Integer, default=0)
    like = Column(Integer, default=0)
    support = Column(Integer, default=0)
    sad = Column(Integer, default=0)

    def __repr__(self):
        return f"<Post {self.post_id}>"

class PostBookmark(Base):
    __tablename__ = 'post_bookmarks'

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id = Column(UUID(as_uuid=True), ForeignKey('posts.uuid'))
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.uuid'))
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now())
    deleted_at = Column(DateTime, nullable=True)

    post = relationship("Post", back_populates="bookmarks")
    user = relationship("User", back_populates="bookmarks")

    def __repr__(self):
        return f"<PostBookmark {self.post.title}>"
    

post_tags = Table(
    'post_tags',
    Base.metadata,
    Column('post_id', UUID(as_uuid=True), ForeignKey('posts.uuid')),
    Column('tag_id', UUID(as_uuid=True), ForeignKey('tags.uuid'))
)



class Notification(Base):
    __tablename__ = 'notifications'

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_generator = Column(UUID(as_uuid=True), ForeignKey('users.uuid'))
    user_receiver = Column(UUID(as_uuid=True), ForeignKey('posts.uuid'))
    post_id = Column(UUID(as_uuid=True), ForeignKey('posts.uuid'))
    title = Column(String(100), nullable=False)
    message = Column(String(255), nullable=False)
    read = Column(Boolean, default=False)
    notification_type = Column(SqlEnum(NotificationType), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
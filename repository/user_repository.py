import uuid
import os
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from models import User, Post, Tag
from api import schemas
from utils import security
from singleton.log import logger
from fastapi import UploadFile
from sqlalchemy import func, select, desc
from repository import post_repository, reaction_repository

TAG = "User Repository -> "
UPLOAD_FOLDER = "static/uploads/profile_pictures"


def create_user(db: Session, user: schemas.UserCreateRequest):
    logger.info("{} create_user called to {}".format(TAG, user.username))
    security.validate_password(user.password, user.confirm_password)
    encrypted_password=security.hash_password(user.password)
    db_user = User(
        username=user.username,
        email=user.email, 
        password=encrypted_password,
        photo=user.photo_url,
        bio=user.bio
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logger.info("{} {} successfully registered in application".format(TAG, user.username))
    return db_user


async def update_user_profile(
    db: AsyncSession,
    user: User,
    username: str,
    email: str,
    bio: str,
    password: str | None,
    confirm_password: str | None,
    profile_picture: UploadFile | None
):
    user.username = username
    user.email = email
    user.bio = bio

    if password and password.strip():
        security.validate_password(password, confirm_password)
        user.password_hash = security.hash_password(password)

    if profile_picture:
        filename = f"{uuid.uuid4().hex}_{profile_picture.filename}"
        save_path = os.path.join(UPLOAD_FOLDER, filename)

        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

        with open(save_path, "wb") as buffer:
            while content := await profile_picture.read(1024):
                buffer.write(content)

        if user.photo_url:
            try:
                old_path = os.path.join(UPLOAD_FOLDER, os.path.basename(user.photo_url))
                if os.path.exists(old_path):
                    os.remove(old_path)
            except Exception as e:
                logger.error("{} Error while trying delete old profile picture".format(TAG, e))

        user.photo_url = f"/{save_path}"

    await db.commit()
    await db.refresh(user)

    return user


async def remove_profile_picture(db: AsyncSession, user: User):
    if user.photo_url:
        try:
            old_path = os.path.join(UPLOAD_FOLDER, os.path.basename(user.photo_url))
            if os.path.exists(old_path):
                os.remove(old_path)
        except Exception as e:
            logger.error("{} Error while trying delete old profile picture".format(TAG, e))

    user.photo_url = None
    await db.commit()
    await db.refresh(user)

    return user

async def get_users_preview(db: AsyncSession, user: User, per_page: int, search: str, offset: int):
    last_post_subq = (
        select(
            Post.user_id,
            func.max(Post.created_at).label("last_post_date")
        )
        .where(Post.deleted_at.is_(None))
        .group_by(Post.user_id)
        .subquery()
    )

    filters = [User.deleted_at.is_(None), User.username != user.username]
    if search:
        filters.append(
            func.or_(
                User.username.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            )
        )

    user_query = (
        select(
            User.uuid,
            User.username,
            User.bio,
            User.photo_url,
            last_post_subq.c.last_post_date
        )
        .outerjoin(last_post_subq, User.uuid == last_post_subq.c.user_id)
        .where(*filters)
        .order_by(User.created_at.desc())
        .offset(offset)
        .limit(per_page)
        .distinct(User.username)
    )

    result = await db.execute(user_query)
    users_raw = result.all()

    response = []

    for user_id, username, bio, photo_url, last_post_date in users_raw:
        top_tags = []

        tag_count_query = (
            select(
                Tag.name,
                Tag.color,
                func.count(Tag.uuid).label("tag_count")
            )
            .select_from(Post)
            .join(Post.tags)
            .where(Post.user_id == user_id, Post.deleted_at.is_(None))
            .group_by(Tag.name, Tag.color)
            .order_by(desc("tag_count"))
            .limit(3)
        )

        tag_result = await db.execute(tag_count_query)
        top_tags = [{"name": row[0], "color": row[1]} for row in tag_result.all()]

        response.append({
            "uuid": user_id,
            "bio": bio,
            "username": username,
            "photo_url": photo_url,
            "last_post_date": last_post_date,
            "top_tags": top_tags
        })

    return response


async def get_user_visit_info(db: AsyncSession, visitor: User, username: str ) -> schemas.UserProfileVisit:
    user = await db.execute(
        select(User).where(User.username == username)
    )   
    user = user.scalars().first()

    if not user:
        return schemas.UserProfileVisit(
            username=None,
            bio=None,
            photo_url=None,
            created_at=None,
            total_posts=0,
            total_reactions=0,
            is_following=False,
            posts_preview=[],
        )
    
    posts = await post_repository.get_posts_preview(
        db=db,
        user=visitor,
        visiting_uuid=user.uuid
    )

    posts_count = await post_repository.post_count_by_user(db, user)
    total_reactions = await reaction_repository.get_user_reactions_count_by_type(db, user)

    return schemas.UserProfileVisit(
        username=user.username,
        bio=user.bio,
        photo_url=user.photo_url,
        created_at=user.created_at,
        total_reactions=total_reactions,
        is_following=False,
        posts_preview=posts,
        total_posts=posts_count
    )


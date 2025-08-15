import models
import uuid
from singleton.log import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, exists, func, and_, select
from sqlalchemy.future import select
from api import schemas

TAG = " Post Repository -> "


async def create_post(
        db: AsyncSession, 
        post: schemas.PostCreateRequest, 
        user: models.User,
        tags: list[models.Tag]
    ) -> models.Post:
    logger.info("{} User {} are trying to create a post {}".format(TAG, user.username, post.title))
    
    db_post = models.Post(
        title=post.title,
        content=post.content,
        user=user
    )
    db_post.tags = tags
    
    db.add(db_post)
    await db.commit()
    await db.refresh(db_post)
    
    logger.info("{} User {} successfully created a post {}".format(TAG, user.username, post.title))
    return db_post


async def get_posts_preview(
        db: AsyncSession, 
        user: models.User, 
        page: int = 1, 
        per_page: int = 10, 
        search: str = None, 
        offset: int = 0,
        bookmarked: bool = False,
        visiting_uuid: str = None
    ) -> list[schemas.PostPreview]:
    
    is_bookmarked = (
        exists()
        .where(
            and_(
                models.PostBookmark.post_id == models.Post.uuid,
                models.PostBookmark.user_id == user.uuid,
                models.PostBookmark.deleted_at.is_(None)
            )
        )
        .label("is_bookmarked")
    )
    user_reaction = (
        select(models.PostReaction.reaction_type)
        .where(
            and_(
                models.PostReaction.post_id == models.Post.uuid,
                models.PostReaction.user_id == user.uuid
            )
        )
        .limit(1)
        .scalar_subquery()
        .label("user_reaction")
    )

    stmt = (
        select(
            models.Post.uuid,
            models.Post.title,
            models.Post.content,
            models.User.username,
            models.Post.created_at,
            is_bookmarked,
            user_reaction, 
            func.group_concat(models.Tag.name, ',').label("tag_names"),
            func.group_concat(models.Tag.color, ',').label("tag_colors"),
            models.PostReactionCount.love,
            models.PostReactionCount.like,
            models.PostReactionCount.support,
            models.PostReactionCount.sad
        )
        .join(models.User, models.Post.user_id == models.User.uuid)
        .outerjoin(models.post_tags, models.post_tags.c.post_id == models.Post.uuid)
        .outerjoin(models.Tag, models.post_tags.c.tag_id == models.Tag.uuid)
        .outerjoin(
            models.PostReactionCount, 
            models.PostReactionCount.post_id == models.Post.uuid
        )
        .group_by(
            models.Post.uuid,
            models.Post.title,
            models.Post.content,
            models.User.username,
            models.Post.created_at,
            models.PostReactionCount.love,
            models.PostReactionCount.like,
            models.PostReactionCount.support,
            models.PostReactionCount.sad
        )
    )
    if visiting_uuid:
        stmt = stmt.where(models.Post.user_id == visiting_uuid)

    # Filtro de busca
    if search:
        search_pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                models.Post.title.ilike(search_pattern),
                models.Post.content.ilike(search_pattern)
            )
        )
    
    stmt = stmt.offset(offset).limit(per_page)
    
    result = await db.execute(stmt)
    rows = result.all()
    
    formatted_posts = []
    for row in rows:

        tag_names = row.tag_names.split(',') if row.tag_names else []
        tag_colors = row.tag_colors.split(',') if row.tag_colors else []

        tags = [
            {"name": name, "color": color}
            for name, color in zip(tag_names, tag_colors)
        ]
        if bookmarked and not row.is_bookmarked:
            continue

        formatted_posts.append({
            "uuid": str(row.uuid),
            "title": row.title,
            "content": row.content,
            "username": row.username,
            "created_at": row.created_at.isoformat(),
            "is_bookmarked": row.is_bookmarked,
            "tags": tags,
            "reactions": {
                "love": row.love or 0,
                "like": row.like or 0,
                "support": row.support or 0,
                "sad": row.sad or 0,
                "user_reaction": row.user_reaction
            }
        })

    return formatted_posts


async def get_post_detail(db: AsyncSession,user: models.User,post_uuid: uuid.UUID) -> schemas.PostDetail: 
    is_bookmarked = (
        exists()
        .where(
            and_(
                models.PostBookmark.post_id == models.Post.uuid,
                models.PostBookmark.user_id == user.uuid,
                models.PostBookmark.deleted_at.is_(None)
            )
        )
        .label("is_bookmarked")
    )

    user_reaction = (
        select(models.PostReaction.reaction_type)
        .where(
            and_(
                models.PostReaction.post_id == models.Post.uuid,
                models.PostReaction.user_id == user.uuid
            )
        )
        .limit(1)
        .scalar_subquery()
        .label("user_reaction")
    )

    stmt = (
        select(
            models.Post.uuid,
            models.Post.title,
            models.Post.content,
            models.User.username,
            models.Post.created_at,
            is_bookmarked,
            user_reaction,
            func.group_concat(models.Tag.name, ',').label("tag_names"),
            func.group_concat(models.Tag.color, ',').label("tag_colors"),
            models.PostReactionCount.love,
            models.PostReactionCount.like,
            models.PostReactionCount.support,
            models.PostReactionCount.sad
        )
        .join(models.User, models.Post.user_id == models.User.uuid)
        .outerjoin(models.post_tags, models.post_tags.c.post_id == models.Post.uuid)
        .outerjoin(models.Tag, models.post_tags.c.tag_id == models.Tag.uuid)
        .outerjoin(
            models.PostReactionCount, 
            models.PostReactionCount.post_id == models.Post.uuid
        )
        .where(models.Post.uuid == post_uuid)
        .group_by(
            models.Post.uuid,
            models.Post.title,
            models.Post.content,
            models.User.username,
            models.Post.created_at,
            models.PostReactionCount.love,
            models.PostReactionCount.like,
            models.PostReactionCount.support,
            models.PostReactionCount.sad
        )
    )
    
    result = await db.execute(stmt)
    row = result.first()
    if not row:
        return None
    
    tag_names = row.tag_names.split(',') if row.tag_names else []
    tag_colors = row.tag_colors.split(',') if row.tag_colors else []
    
    tags = [
        {"name": name, "color": color}
        for name, color in zip(tag_names, tag_colors)
    ]
    return {
        "uuid": str(row.uuid),
        "title": row.title,
        "content": row.content,
        "username": row.username,
        "created_at": row.created_at.isoformat(),
        "is_bookmarked": row.is_bookmarked,
        "tags": tags,
        "reactions": {
            "love": row.love or 0,
            "like": row.like or 0,
            "support": row.support or 0,
            "sad": row.sad or 0,
            "user_reaction": row.user_reaction
        }
    }


async def post_bookmark(db: AsyncSession, db_post: models.Post, user: models.User) -> bool:
    logger.info("{} User {} are trying to bookmark a post {}".format(TAG, user.username, db_post.title))
    
    stmt = select(models.PostBookmark).where(
        and_(
            models.PostBookmark.post_id == db_post.uuid,
            models.PostBookmark.user_id == user.uuid
        )
    )
    result = await db.execute(stmt)
    db_bookmark = result.scalar_one_or_none()
    
    logger.info("{} Post {} found for user {}".format(TAG, db_post.title, user.username))
    
    if db_bookmark:
        await db.delete(db_bookmark)
        await db.commit()
        response = False
    else:
        new_bookmark = models.PostBookmark(post_id=db_post.uuid, user_id=user.uuid)
        db.add(new_bookmark)
        await db.commit()
        await db.refresh(new_bookmark)
        response = True

    logger.info("{} Response to bookmark post {} by user {}: {}".format(
        TAG, db_post.title, user.username, response
    ))
    return response


async def post_count_by_user(db: AsyncSession, user: models.User):
    stmt = select(func.count(models.Post.uuid)).where(models.Post.user_id == user.uuid)
    result = await db.execute(stmt)
    return result.scalar()

async def post_reaction(db: AsyncSession, db_post: models.Post, user: models.User, reaction: str) -> bool:
    logger.info("{} User {} are trying to react a post {}".format(TAG, user.username, db_post.title))



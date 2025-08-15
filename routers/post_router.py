from repository import post_repository, reaction_repository, tag_repository
from services import auth_service, notification_service
import models

from uuid import UUID
from fastapi import  Depends, HTTPException, status, Cookie, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.future import select
from api import schemas
from singleton.db import get_async_db
from singleton.router import router



@router.get("/posts/preview", response_model=list[schemas.PostPreview])
async def get_posts(
    db: AsyncSession = Depends(get_async_db),
    access_token: str | None = Cookie(default=None),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    search: str = Query(None)
):
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing access token")

    user = await auth_service.get_user_by_token(db, access_token)

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    offset = (page - 1) * per_page
    response = await post_repository.get_posts_preview(db, user, page, per_page, search, offset)
    return response


@router.post("/posts/create", status_code=status.HTTP_201_CREATED, response_model=str)
async def create_post(
    post_payload: schemas.PostCreateRequest,
    db: AsyncSession = Depends(get_async_db),
    access_token: str | None = Cookie(default=None),
):
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing access token")

    user = await auth_service.get_user_by_token(db, access_token)

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    tags = await tag_repository.get_tags_by_uuid_async(db, post_payload.categories)
    if not tags:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tags not found")

    db_post = await post_repository.create_post(db, post_payload, user, tags)
    return str(db_post.uuid)

@router.get("/post/detail/{uuid}", response_model=schemas.PostDetail)
async def get_post(
    uuid: str,
    db: AsyncSession = Depends(get_async_db),
    access_token: str | None = Cookie(default=None)
    ):

    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing access token")
    
    user = await auth_service.get_user_by_token(db, access_token)

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    
    db_post = await post_repository.get_post_detail(db, user, UUID(uuid))
    if not db_post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    
    return db_post



@router.get("/posts/{post_uuid}/bookmark", status_code=status.HTTP_201_CREATED, response_model=bool)
async def bookmark_post(
    post_uuid: str, 
    db: AsyncSession = Depends(get_async_db), 
    access_token: str | None = Cookie(default=None)
):
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing access token")
    
    user = await auth_service.get_user_by_token(db, access_token)

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    post_result = await db.execute(select(models.Post).where(models.Post.uuid == UUID(post_uuid)))
    db_post = post_result.scalar_one_or_none()
    
    if not db_post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    
    try:
        bookmarked = await post_repository.post_bookmark(db, db_post, user)
        if bookmarked:
            await notification_service.create_bookmark_notification(db, db_post, user)
        return bookmarked
    except Exception as e:
        import traceback
        traceback.print_exc()
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing bookmark: {str(e)}"
        )

@router.post("/posts/reaction", status_code=status.HTTP_201_CREATED, response_model=schemas.ReactionResponse)
async def reaction_post(
        reaction_payload: schemas.ReactionRequest,
        db: AsyncSession = Depends(get_async_db),
        access_token: str | None = Cookie(default=None)
    ):
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing access token")
    
    user = await auth_service.get_user_by_token(db, access_token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    
    post_result = await db.execute(select(models.Post).where(models.Post.uuid == UUID(reaction_payload.post_uuid)))
    db_post = post_result.scalar_one_or_none()
    
    if not db_post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    
    await notification_service.create_reaction_notification(db, db_post, user, reaction_payload.reaction)
    return await reaction_repository.create_post_reaction(db, db_post, user, reaction_payload.reaction)


@router.get("/posts/bookmarked", response_model=list[schemas.PostPreview])
async def bookmarked_posts(
        db: AsyncSession = Depends(get_async_db),
        access_token: str | None = Cookie(default=None),
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=100),
        search: str = Query(None)
    ):
        if not access_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing access token")

        user = await auth_service.get_user_by_token(db, access_token)

        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
        offset = (page - 1) * per_page
        return await post_repository.get_posts_preview(db, user, page, per_page, search, offset, bookmarked=True)
        

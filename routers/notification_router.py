
from fastapi import Depends, HTTPException, status, Cookie
from sqlalchemy.ext.asyncio import AsyncSession
from api import schemas
from services import auth_service
from singleton.db import  get_async_db
from singleton.router import router
from repository import notification_repository


@router.get("/notifications/count", status_code=status.HTTP_200_OK)
async def notifications(
        db: AsyncSession = Depends(get_async_db),
        access_token: str | None = Cookie(default=None),
):
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing access token")

    user = await auth_service.get_user_by_token(db, access_token)

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    
    return await notification_repository.get_notifications_count(db, user)


@router.get("/notifications", response_model=list[schemas.NotificationResponse], status_code=status.HTTP_200_OK)
async def notifications(
        db: AsyncSession = Depends(get_async_db),
        access_token: str | None = Cookie(default=None),
):
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing access token")

    user = await auth_service.get_user_by_token(db, access_token)

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    
    return await notification_repository.get_notifications(db, user)
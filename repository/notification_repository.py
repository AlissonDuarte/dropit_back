import models
import uuid
from singleton.log import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.future import select
from api import schemas


TAG = "Notification Repository -> "

async def create_notification(
        db: AsyncSession,
        notification: schemas.NotificationCreateRequest,

    ):
    notification_type_map = {
        "att": models.NotificationType.ATT,
        "new": models.NotificationType.NEW
    }

    logger.info("{} User {} are trying to create a notification {}".format(
        TAG, 
        notification.user_generator, 
        notification.title
        )
    )

    user_generator = await db.scalar(
        select(models.User).where(models.User.uuid == notification.user_generator)
    )

    if not user_generator:
        logger.error("{} User to generate this notification does not exist".format(TAG))
        raise Exception("User to generate this notification does not exist")
    
    user_receiver = await db.scalar(
        select(models.User).where(models.User.uuid == notification.user_receiver)
    )
    if not user_receiver:
        logger.error("{} User to receive this notification does not exist".format(TAG))
        raise Exception("User to receive this notification does not exist")

    post_exists = await db.scalar(
        select(models.Post).where(models.Post.uuid == notification.post_id)
    )

    if not post_exists:
        logger.error("{} Post does not exist".format(TAG))
        raise Exception("Post does not exist")
    
    db_notification = models.Notification(
        user_generator=user_generator.uuid,
        user_receiver=user_receiver.uuid,
        post_id=notification.post_id,
        title=notification.title,
        message=notification.content,
        notification_type=notification_type_map.get(notification.notification_type, models.NotificationType.NEW)
    )

    db.add(db_notification)
    await db.commit()
    await db.refresh(db_notification)

    logger.info("{} User {} successfully created a notification {}".format(
        TAG, 
        notification.user_generator, 
        notification.title
        )
    )

    return db_notification


async def get_notifications(db: AsyncSession, user: models.User):
    stmt = select(models.Notification).where(
        models.Notification.user_receiver == user.uuid,
        models.Notification.deleted_at.is_(None),
    ).order_by(models.Notification.created_at.desc())
    result = await db.execute(stmt)
    notifications = result.scalars().all()
    for notification in notifications:
        notification.read = True
    
    await db.commit()
    return notifications


async def get_notifications_count(db: AsyncSession, user: models.User):
    stmt = select(func.count(models.Notification.uuid)).where(
        models.Notification.user_receiver == user.uuid,
        models.Notification.deleted_at.is_(None),
        models.Notification.read == False
    )
    result = await db.execute(stmt)
    return result.scalar()
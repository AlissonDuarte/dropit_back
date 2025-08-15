from uuid import UUID
from api.schemas import NotificationCreateRequest
from repository import notification_repository
from sqlalchemy.ext.asyncio import AsyncSession
from models import Post, User
from singleton.log import logger


TAG = "Notification Service -> "

async def _create_notification(
        db: AsyncSession,
        user_generator: User,
        user_receiver: UUID,
        post_id: UUID,
        content: str,
        notification_type: str = "att",
        title: str = "Nova mensagem"
    ) -> None:

    try:
        notification_schema = NotificationCreateRequest(
            title=title,
            content=content,
            notification_type=notification_type,
            user_generator=user_generator.uuid,
            user_receiver=user_receiver,
            post_id=post_id
        )
        
        await notification_repository.create_notification(db, notification_schema)
    except Exception as e:
        await db.rollback()
        logger.error(f"{TAG} Error while handling notification: {e}")


async def create_bookmark_notification(
        db: AsyncSession, 
        post: Post,
        user_generator: User
    ) -> None:
    content = f"O usuário {user_generator.username} salvou o seu post '{post.title}' como favorito"
    await _create_notification(
        db=db,
        user_generator=user_generator,
        user_receiver=post.user_id,
        post_id=post.uuid,
        content=content
    )


async def create_reaction_notification(
        db: AsyncSession, 
        post: Post,
        user_generator: User,
        reaction: str
    ) -> None:
    content = f"O usuário {user_generator.username} reagiu ao seu post '{post.title}' com '{reaction}'"
    await _create_notification(
        db=db,
        user_generator=user_generator,
        user_receiver=post.user_id,
        post_id=post.uuid,
        content=content
    )
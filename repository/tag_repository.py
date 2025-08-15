from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import models
import uuid

TAG = "Tag Repository -> "


def get_tag_by_uuid(db: Session, uuid: str) -> models.Tag:
    return db.query(models.Tag).filter(models.Tag.uuid == uuid).first()

def get_tags_by_uuid(db: Session, uuid_list: list[str]) -> list[models.Tag]:
    uuid_list = [uuid.UUID(item) for item in uuid_list]
    return db.query(models.Tag).filter(models.Tag.uuid.in_(uuid_list)).all()

async def get_tags_by_uuid_async(db: AsyncSession, uuid_list: list[str]) -> list[models.Tag]:
    uuid_objects = [uuid.UUID(item) for item in uuid_list]
    
    # Executa a query assíncrona
    result = await db.execute(
        select(models.Tag)
        .where(models.Tag.uuid.in_(uuid_objects))
    )
    
    return result.scalars().all()

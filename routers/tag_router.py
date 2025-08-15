import models
from fastapi import status
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from api import schemas
from singleton.db import get_db
from singleton.router import router


@router.get("/categories", response_model=list[schemas.Tag])
async def get_categories(db: Session = Depends(get_db)):
    return db.query(models.Tag).filter(models.Tag.active == True).all()


# @router.post("/bulk_create_tags", status_code=status.HTTP_201_CREATED)
# async def bulk_create_tags(tag_payload: list[schemas.TagCreateRequest], db: Session = Depends(get_db)):
#     for tag in tag_payload:
#         db_tag = db.query(models.Tag).filter(models.Tag.name == tag.name).first()
#         if not db_tag:
#             db_tag = models.Tag(name=tag.name, group=tag.group, color=tag.color)
#             db.add(db_tag)
#     db.commit()
#     return
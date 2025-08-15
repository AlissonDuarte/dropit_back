import jwt
import os
import datetime
import uuid
import models
from dotenv import load_dotenv
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

load_dotenv()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "secret")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

def create_access_token(user_uuid: str, remember: bool = False) -> dict[str, str]:
    if remember:
        expire=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30)
    else:
        expire=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
    
    to_encode={
        "sub": user_uuid,
        "exp": expire
    }
    token=jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    response={
        "access_token": token,
        "token_type": "bearer",
        "exp": expire
    }
    return response


def verify_token(token:str = Depends(oauth2_scheme)) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_uuid_raw: str = payload.get("sub")
        if user_uuid_raw is None:
            raise HTTPException(status_code=401, detail="Invalid user")
        try:
           user_uuid = uuid.UUID(user_uuid_raw)
        except ValueError:
            raise HTTPException(status_code=401, detail="Invalid decoded information")
        return user_uuid
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token: {}".format(e))


async def get_user_by_token(db: AsyncSession, access_token: str) -> models.User:
    user_uuid = verify_token(access_token)
    stmt = select(models.User).where(models.User.uuid == user_uuid)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
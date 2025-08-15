import models
import uuid
from fastapi import Depends, HTTPException,  UploadFile, File, Form, status, Cookie, Query
from fastapi.responses import JSONResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from api import schemas
from utils import security
from services import auth_service
from singleton.db import get_db, get_async_db
from singleton.router import router
from repository import user_repository


@router.get("/user/alive", status_code=status.HTTP_200_OK)
async def alive():
    return {"message": "Alive"}

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    email: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    bio: str = Form(""),
    photo: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(
        or_(
            models.User.email == email,
            models.User.username == username
        )
    ).first()
    if user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User with this email or username already exists")

    photo_url = None
    if photo:
        filename = f"profile_pics/{uuid.uuid4()}_{photo.filename}"
        contents = await photo.read()
        with open(filename, "wb") as f:
            f.write(contents)
        photo_url = f"/static/{filename}"

    user_data = schemas.UserCreateRequest(
        username=username,
        email=email,
        password=password,
        confirm_password=confirm_password,
        bio=bio,
        photo_url=photo_url
    )

    user_repository.create_user(db, user_data)

    return HTTPException(detail="User successfully registered", status_code=status.HTTP_201_CREATED)

@router.post("/login", response_model=schemas.LoginResponse)
async def login(user_credentials: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(
        models.User.email == user_credentials.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User Not Found")
    
    if not security.verify_password(user_credentials.password, user.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials")
    token_data = auth_service.create_access_token(user_uuid=str(user.uuid), remember=user_credentials.remember)
    access_token = token_data["access_token"]
    max_age = token_data["exp"]

    response = JSONResponse(content={"message": "Login successful"})
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=max_age,
        expires=max_age,
        samesite="Lax",
        secure=False
    )
    return response


@router.get("/user/profile", response_model=schemas.UserProfile)
async def get_profile(db: AsyncSession = Depends(get_async_db), access_token: str | None = Cookie(default=None)):
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing access token")

    user = await auth_service.get_user_by_token(db, access_token)

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    
    return user

@router.patch("/user/profile", response_model=schemas.UserProfile)
async def update_profile(
    username: str = Form(...),
    email: str = Form(...),
    bio: str = Form(...),
    password: str = Form(None),
    confirm_password: str = Form(None),
    profile_picture: UploadFile = File(None),
    db: AsyncSession = Depends(get_async_db),
    access_token: str | None = Cookie(default=None)
):
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing access token")

    user = await auth_service.get_user_by_token(db, access_token)

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    response = await user_repository.update_user_profile(db, user, username, email, bio, password, confirm_password, profile_picture)
    return response

@router.patch("/user/profile/remove_picture")
async def remove_profile_picture(
    db: AsyncSession = Depends(get_async_db),
    access_token: str | None = Cookie(default=None)
    ):
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing access token")

    user = await auth_service.get_user_by_token(db, access_token)

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    response = await user_repository.remove_profile_picture(db, user)
    return response


@router.get("/users/preview", response_model=list[schemas.UserPreview])
async def get_users_preview(
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
    response = await user_repository.get_users_preview(db, user, per_page, search, offset)
    return response


@router.get("/user/visit/{username}", response_model=schemas.UserProfileVisit)
async def get_user_profile_vist_info(
        username: str,
        access_token: str | None = Cookie(default=None),
        db: AsyncSession = Depends(get_async_db)
    ):

    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing access token")

    user = await auth_service.get_user_by_token(db, access_token)

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    if user.username == username:
        raise HTTPException(status_code=status.HTTP_307_TEMPORARY_REDIRECT, detail="You can't visit your own profile")
    
    return await user_repository.get_user_visit_info(db, user, username)
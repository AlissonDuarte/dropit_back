from fastapi import FastAPI
from database import Base, sync_engine
from routers import user_router, tag_router, post_router, notification_router
from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles

load_dotenv()

Base.metadata.create_all(bind=sync_engine)


app = FastAPI()

app.include_router(post_router.router, prefix="/api")
app.include_router(user_router.router, prefix="/api")
app.include_router(tag_router.router, prefix="/api")
app.include_router(notification_router.router, prefix="/api")
app.mount("/static", StaticFiles(directory="static"), name="static")
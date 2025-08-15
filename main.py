from fastapi import FastAPI
from database import Base, sync_engine
from routers import user_router, tag_router, post_router, notification_router
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

load_dotenv()

Base.metadata.create_all(bind=sync_engine)


app = FastAPI()
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://192.168.1.50:5173",
    "http://172.18.0.1:5173",
    "http://172.19.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(post_router.router, prefix="/api")
app.include_router(user_router.router, prefix="/api")
app.include_router(tag_router.router, prefix="/api")
app.include_router(notification_router.router, prefix="/api")
app.mount("/static", StaticFiles(directory="static"), name="static")